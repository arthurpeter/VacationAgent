import math
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional
from app.core.logger import get_logger
import json

log = get_logger(__name__)

class ScheduleEngine:
    def __init__(self, pace: str, arrival_dt: datetime, departure_dt: datetime, 
                 hotel_coords: tuple, airport_coords: tuple,
                 wakeup_time: str = "08:00", lunch_duration_mins: int = 90):
        
        self.pace = pace.lower()
        self.arrival_dt = arrival_dt
        self.departure_dt = departure_dt
        self.hotel_coords = hotel_coords
        self.airport_coords = airport_coords
        self.lunch_duration_mins = lunch_duration_mins
        self.arrival_buffer_hours = 3.5 
        
        wakeup_t = datetime.strptime(wakeup_time, "%H:%M").time()
        self.morning_start_delta = timedelta(hours=wakeup_t.hour, minutes=wakeup_t.minute) + timedelta(minutes=90)
        
        self.priority_weights = {"must": 3, "want": 2, "optional": 1}
        
        # Density mapping controls the Soft Budget
        self.density_mapping = {
            "relaxed": 0.70,   
            "moderate": 0.85,  
            "fast-paced": 1.0  
        }
        self.density_factor = self.density_mapping.get(self.pace, 0.85)
        
        self.base_hard_budget_mins = 9 * 60 
        self.hard_day_cutoff = time(20, 0) 
        self.base_padding_mins = 30

    def _calculate_distance_degrees(self, lat1, lon1, lat2, lon2):
        return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

    def _get_base_transit_mins(self, lat1, lon1, lat2, lon2):
        dist_degrees = self._calculate_distance_degrees(lat1, lon1, lat2, lon2)
        # ~70 mins per degree accounts for inter-city travel 
        return self.base_padding_mins + int(dist_degrees * 70) 

    def _get_effective_costs(self, raw_duration: int, raw_transit: int, rigidity: float) -> tuple[int, int, int]:
        """
        Applies dynamic inflation based on the schedule rigidity.
        Rigidity = 1.0 (Excursions) -> No inflation, strict packing.
        Rigidity = 0.0 (City stays) -> Inflated transit, switch penalties added for natural slack.
        """
        slack_factor = {"relaxed": 0.3, "moderate": 0.15, "fast-paced": 0.0}.get(self.pace, 0.15)
        
        inflation = 1.0 + (slack_factor * (1.0 - rigidity))
        effective_transit = int(raw_transit * inflation)
        
        switch_penalty = int(15 * (1.0 - rigidity))
        
        effective_total_cost = raw_duration + effective_transit + switch_penalty
        return effective_total_cost, effective_transit, switch_penalty

    def _is_open_interval(self, arrival_dt: datetime, departure_dt: datetime, opening_hours_str: str) -> tuple[bool, bool]:
        if not opening_hours_str: return True, True 
        day_of_week = arrival_dt.strftime('%A').lower()
            
        try:
            if isinstance(opening_hours_str, str):
                hours_dict = json.loads(opening_hours_str)
            elif isinstance(opening_hours_str, dict):
                hours_dict = opening_hours_str
            else:
                return True, True

            day_hours = hours_dict.get(day_of_week)
            if day_hours is None or str(day_hours).lower() == "null": return True, True
            if "closed" in str(day_hours).lower(): return False, False
            if "24" in str(day_hours).lower() or "00:00-24:00" in str(day_hours): return True, False
            if "-" in str(day_hours):
                open_str, close_str = str(day_hours).split("-")
                open_t = datetime.strptime(open_str.strip(), "%H:%M").time()
                close_t = datetime.strptime(close_str.strip(), "%H:%M").time()
                arr_t = arrival_dt.time()
                dep_t = departure_dt.time()
                if open_t <= close_t: return (open_t <= arr_t and dep_t <= close_t), False
                else: return (arr_t >= open_t or dep_t <= close_t), False
        except Exception as e:
            log.warning(f"Failed to parse opening hours: {e} | Data: {opening_hours_str}")
            return True, True 
        return True, False

    def _score_poi(self, poi: dict, current_loc: tuple, active_time: int, soft_budget: int, hard_budget: int, eff_cost: int) -> float:
        """
        The Unified Scoring Model.
        Balances Priority, Geographic proximity, and Budget Constraints.
        """
        score = poi['priority_score'] * 1000 
        
        dist = self._calculate_distance_degrees(current_loc[0], current_loc[1], poi['latitude'], poi['longitude'])
        score -= (dist * 500)
        
        if active_time + eff_cost > soft_budget:
            if poi['bucket'] != 'must':
                score -= 5000 
            else:
                score -= 500  
                
        return score

    # Helper function to compute matching transit metadata with clean fallbacks
    def _resolve_transit_leg(self, lat1: float, lon1: float, lat2: float, lon2: float, 
                             transit_lookup: dict, default_mins: int) -> tuple[int, dict]:
        leg_key = f"{lat1:.5f},{lon1:.5f}->{lat2:.5f},{lon2:.5f}"
        if leg_key in transit_lookup:
            leg_meta = transit_lookup[leg_key]
            active_mode = leg_meta.get("active_mode", "transit")
            mode_bundle = leg_meta.get("alternatives", {}).get(active_mode, {})
            
            raw_transit = mode_bundle.get("duration_mins", default_mins)
            buffer = 5 if active_mode in ["transit", "uber", "driving"] else 0
            
            return (raw_transit + buffer), {
                "is_verified": True,
                "mode": active_mode,
                "polyline": mode_bundle.get("polyline"),
                "steps": mode_bundle.get("steps", []),
                "distance_text": mode_bundle.get("distance_text", "")
            }
        
        return default_mins, {
            "is_verified": False,
            "mode": "estimated",
            "polyline": None,
            "steps": [],
            "distance_text": ""
        }

    # --- UPGRADED GEOGRAPHIC OPTIMIZER LOOP ---
    def generate_schedule(self, pois: List[Dict[str, Any]], 
                          existing_transit_legs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not pois: return {"status": "success", "schedule": [], "excluded": {}}
        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        
        transit_lookup = existing_transit_legs or {}

        for p in pois:
            p['bucket'] = p.get('bucket', 'want').lower()
            p['priority_score'] = self.priority_weights.get(p['bucket'], 2)

        # --- MACRO REGION CLASSIFICATION ---
        home_pois = []
        excursion_pois = []
        for p in pois:
            if self._calculate_distance_degrees(self.hotel_coords[0], self.hotel_coords[1], p['latitude'], p['longitude']) > 0.5:
                excursion_pois.append(p)
            else:
                home_pois.append(p)

        active_days = list(range(total_days))
        if not active_days: return {"status": "error"}

        full_days = [i for i in active_days if i != 0 and i != total_days - 1]
        excursion_day_map = {}
        
        if excursion_pois and len(full_days) >= 1:
            excursion_day_idx = full_days[len(full_days) // 2]
            excursion_day_map[excursion_day_idx] = excursion_pois
            
        schedule = []
        unassigned_pois = list(pois)

        # --- THE OPTIMIZER LOOP ---
        for day_idx in active_days:
            is_excursion = day_idx in excursion_day_map
            rigidity = 1.0 if is_excursion else 0.0
            
            day_density = 1.0 if is_excursion else self.density_factor
            soft_budget = int(self.base_hard_budget_mins * day_density)
            hard_budget = self.base_hard_budget_mins
            
            current_date = self.arrival_dt.date() + timedelta(days=day_idx)
            
            # Smart Clock Initialization
            standard_wakeup = datetime.combine(current_date, time()) + self.morning_start_delta
            if day_idx == 0:
                current_clock = max(self.arrival_dt + timedelta(hours=self.arrival_buffer_hours), standard_wakeup)
            elif day_idx == total_days - 1:
                leave_for_airport = self.departure_dt - timedelta(hours=3)
                current_clock = min(standard_wakeup, leave_for_airport)
            else:
                current_clock = standard_wakeup
            
            end_clk = (self.departure_dt - timedelta(hours=3)) if day_idx == total_days - 1 else datetime.combine(current_date, self.hard_day_cutoff)

            current_loc = self.hotel_coords
            active_time_spent = 0
            lunch_taken = False
            day_plan = []

            # --- 1. INJECT START ANCHORS ---
            if day_idx == 0:
                airport_dep = self.arrival_dt + timedelta(minutes=45)
                day_plan.append({
                    "type": "attraction", "id": "arr_airport", "name": "Arrive at Airport", "bucket": "logistics",
                    "start_time": self.arrival_dt.strftime("%H:%M"), "end_time": airport_dep.strftime("%H:%M"),
                    "transit_mins": 0, "unknown_hours_warning": False,
                    "latitude": self.airport_coords[0], "longitude": self.airport_coords[1]
                })

                # Check for verified arrival transit leg
                h_transit, h_leg = self._resolve_transit_leg(
                    self.airport_coords[0], self.airport_coords[1], 
                    self.hotel_coords[0], self.hotel_coords[1], transit_lookup, 45
                )
                hotel_arr = airport_dep + timedelta(minutes=h_transit)
                day_plan.append({
                    "type": "attraction", "id": "arr_hotel", "name": "Transit & Check-in at Hotel", "bucket": "logistics",
                    "start_time": airport_dep.strftime("%H:%M"), "end_time": hotel_arr.strftime("%H:%M"),
                    "transit_mins": h_transit, "unknown_hours_warning": False,
                    "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1],
                    "transit_leg": h_leg
                })
                current_clock = max(current_clock, hotel_arr)
            else:
                day_plan.append({
                    "type": "attraction", "id": f"start_hotel_{day_idx}", "name": "Start Day at Hotel", "bucket": "logistics",
                    "start_time": current_clock.strftime("%H:%M"), "end_time": (current_clock + timedelta(minutes=5)).strftime("%H:%M"),
                    "transit_mins": 0, "unknown_hours_warning": False,
                    "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1]
                })
                current_clock += timedelta(minutes=5)
            
            daily_pool = excursion_day_map[day_idx] if is_excursion else [p for p in unassigned_pois if p in home_pois]
            
            # --- ATTRACTION SELECTION ---
            while daily_pool and current_clock < end_clk:
                if current_clock.hour >= 13 and not lunch_taken:
                    day_plan.append({
                        "type": "meal", "name": "Lunch Break",
                        "start_time": current_clock.strftime("%H:%M"),
                        "end_time": (current_clock + timedelta(minutes=self.lunch_duration_mins)).strftime("%H:%M")
                    })
                    current_clock += timedelta(minutes=self.lunch_duration_mins)
                    lunch_taken = True
                    continue
                
                best_candidate = None
                best_score = -float('inf')
                
                for p in daily_pool:
                    raw_dur = p.get('recommended_duration_mins', 120)
                    
                    # Resolve real transit metrics
                    est_mins = self._get_base_transit_mins(current_loc[0], current_loc[1], p['latitude'], p['longitude'])
                    transit_mins, leg_state = self._resolve_transit_leg(
                        current_loc[0], current_loc[1], p['latitude'], p['longitude'], transit_lookup, est_mins
                    )

                    eff_total, eff_transit, switch_pen = self._get_effective_costs(raw_dur, transit_mins, rigidity)
                    arr_dt = current_clock + timedelta(minutes=eff_transit)
                    
                    wait_mins = 0
                    valid_arr, valid_dep, is_unk = None, None, False
                    
                    while wait_mins <= 90:
                        test_arr = arr_dt + timedelta(minutes=wait_mins)
                        test_dep = test_arr + timedelta(minutes=raw_dur + switch_pen)
                        
                        if test_dep > end_clk or (active_time_spent + eff_total > hard_budget): break
                            
                        is_open, unk = self._is_open_interval(test_arr, test_dep, p.get("opening_hours"))
                        if is_open:
                            valid_arr, valid_dep, is_unk = test_arr, test_dep, unk
                            break
                        wait_mins += 30
                        
                    if not valid_arr: continue
                        
                    score = self._score_poi(p, current_loc, active_time_spent, soft_budget, hard_budget, eff_total)
                    if score > best_score:
                        best_score = score
                        best_candidate = {
                            "poi": p, "arr": valid_arr, "dep": valid_dep, 
                            "wait": wait_mins, "eff_total": eff_total, "unk": is_unk, 
                            "transit_mins": transit_mins, "leg_state": leg_state
                        }
                
                if not best_candidate:
                    current_clock += timedelta(minutes=30)
                    continue
                    
                b_poi = best_candidate['poi']
                if best_candidate['wait'] > 0:
                    day_plan.append({
                        "type": "free_time", "name": "Free Time / Wait for Opening",
                        "start_time": (best_candidate['arr'] - timedelta(minutes=best_candidate['wait'])).strftime("%H:%M"),
                        "end_time": best_candidate['arr'].strftime("%H:%M")
                    })

                day_plan.append({
                    "type": "attraction", "id": b_poi['id'], "name": b_poi['name'], "bucket": b_poi['bucket'],
                    "start_time": best_candidate['arr'].strftime("%H:%M"), 
                    "end_time": (best_candidate['arr'] + timedelta(minutes=b_poi.get('recommended_duration_mins', 120))).strftime("%H:%M"),
                    "transit_mins": best_candidate['transit_mins'], "unknown_hours_warning": best_candidate['unk'],
                    "latitude": b_poi['latitude'], "longitude": b_poi['longitude'], "image_url": b_poi.get('image_url'),
                    "transit_leg": best_candidate['leg_state'] # Inject data object structure
                })
                
                current_clock = best_candidate['dep']
                current_loc = (b_poi['latitude'], b_poi['longitude'])
                active_time_spent += best_candidate['eff_total']
                
                daily_pool = [p for p in daily_pool if p['id'] != b_poi['id']]
                unassigned_pois = [p for p in unassigned_pois if p['id'] != b_poi['id']]

            # --- 2. INJECT RETURN TO HOTEL ANCHOR ---
            if active_time_spent > 0:
                est_ret_mins = self._get_base_transit_mins(current_loc[0], current_loc[1], self.hotel_coords[0], self.hotel_coords[1])
                ret_transit_mins, ret_leg = self._resolve_transit_leg(
                    current_loc[0], current_loc[1], self.hotel_coords[0], self.hotel_coords[1], transit_lookup, est_ret_mins
                )
                return_dt = current_clock + timedelta(minutes=ret_transit_mins)
                
                day_plan.append({
                    "type": "attraction", "id": f"return_hotel_{day_idx}", "name": "Return to Hotel", "bucket": "logistics",
                    "start_time": current_clock.strftime("%H:%M"), "end_time": return_dt.strftime("%H:%M"),
                    "transit_mins": ret_transit_mins, "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1],
                    "unknown_hours_warning": False,
                    "transit_leg": ret_leg # Handles tracking return metrics smoothly!
                })
                current_clock = return_dt

            # --- 3. INJECT AIRPORT DEPARTURE ANCHOR (LAST DAY) ---
            if day_idx == total_days - 1:
                leave_for_airport_time = self.departure_dt - timedelta(hours=3)
                
                if current_clock < leave_for_airport_time:
                    day_plan.append({
                        "type": "free_time", "id": "free_time_hotel", "name": "Relax at Hotel / Grab Bags",
                        "start_time": current_clock.strftime("%H:%M"), "end_time": leave_for_airport_time.strftime("%H:%M")
                    })
                
                est_dep_mins = self._get_base_transit_mins(self.hotel_coords[0], self.hotel_coords[1], self.airport_coords[0], self.airport_coords[1])
                dep_transit_mins, dep_leg = self._resolve_transit_leg(
                    self.hotel_coords[0], self.hotel_coords[1], self.airport_coords[0], self.airport_coords[1], transit_lookup, est_dep_mins
                )
                
                day_plan.append({
                    "type": "attraction", "id": "dep_airport", "name": "Transit to Airport & Depart", "bucket": "logistics",
                    "start_time": leave_for_airport_time.strftime("%H:%M"), "end_time": self.departure_dt.strftime("%H:%M"),
                    "transit_mins": dep_transit_mins, "latitude": self.airport_coords[0], "longitude": self.airport_coords[1],
                    "unknown_hours_warning": False,
                    "transit_leg": dep_leg
                })

            if day_plan:
                schedule.append({"day_index": day_idx, "date": current_date.strftime("%Y-%m-%d"), "events": day_plan})

        # --- EXCLUDED ---
        excluded = {"must": [], "want": [], "optional": []}
        for p in unassigned_pois: 
            excluded[p['bucket']].append({"id": p["id"], "name": p["name"], "bucket": p['bucket'], "type": "attraction"})
            
        return {"status": "success", "schedule": schedule, "excluded": excluded}
    
    def recalculate_user_timeline(
        self, 
        user_days_poi_ids: List[List[int]], 
        pois: List[Dict[str, Any]], 
        existing_transit_legs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Bypasses the optimizer to map strict custom layout arrays.
        Matches consecutive location nodes against existing_transit_legs coordinate pairs:
        - If matched: Employs verified Google metadata options + padding buffers.
        - If unmatched (Cache Miss from a custom Drag Event): Employs haversine fast-math estimates.
        """
        poi_map = {p['id']: p for p in pois}
        schedule = []
        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        
        # Fallback dictionary to avoid missing parameter runtime errors
        transit_lookup = existing_transit_legs or {}
        
        for day_idx, day_poi_ids in enumerate(user_days_poi_ids):
            current_date = self.arrival_dt.date() + timedelta(days=day_idx)
            
            # Clock Init
            standard_wakeup = datetime.combine(current_date, time()) + self.morning_start_delta
            if day_idx == 0:
                current_clock = max(self.arrival_dt + timedelta(hours=self.arrival_buffer_hours), standard_wakeup)
            elif day_idx == total_days - 1:
                leave_for_airport = self.departure_dt - timedelta(hours=3)
                current_clock = min(standard_wakeup, leave_for_airport)
            else:
                current_clock = standard_wakeup
                
            current_loc = self.hotel_coords
            lunch_taken = False
            day_plan = []
            
            # 1. INJECT START ARRIVAL LOGISTICS
            if day_idx == 0:
                airport_dep = self.arrival_dt + timedelta(minutes=45)
                
                # Check for verified arrival leg
                arr_key = f"{self.airport_coords[0]:.5f},{self.airport_coords[1]:.5f}->{self.hotel_coords[0]:.5f},{self.hotel_coords[1]:.5f}"
                arr_transit_mins = 45
                arr_leg_payload = {"is_verified": False, "mode": "estimated", "polyline": None, "steps": []}
                
                if arr_key in transit_lookup:
                    active_mode = transit_lookup[arr_key].get("active_mode", "driving")
                    mode_data = transit_lookup[arr_key].get("alternatives", {}).get(active_mode, {})
                    arr_transit_mins = mode_data.get("duration_mins", 45) + 5 # Add ride buffer
                    arr_leg_payload = {"is_verified": True, "mode": active_mode, "polyline": mode_data.get("polyline"), "steps": mode_data.get("steps", [])}
                
                day_plan.append({
                    "type": "attraction", "id": "arr_airport", "name": "Arrive at Airport", "bucket": "logistics",
                    "start_time": self.arrival_dt.strftime("%H:%M"), "end_time": airport_dep.strftime("%H:%M"),
                    "transit_mins": 0, "unknown_hours_warning": False, "latitude": self.airport_coords[0], "longitude": self.airport_coords[1]
                })
                
                hotel_arr = airport_dep + timedelta(minutes=arr_transit_mins)
                day_plan.append({
                    "type": "attraction", "id": "arr_hotel", "name": "Transit & Check-in at Hotel", "bucket": "logistics",
                    "start_time": airport_dep.strftime("%H:%M"), "end_time": hotel_arr.strftime("%H:%M"),
                    "transit_mins": arr_transit_mins, "unknown_hours_warning": False, 
                    "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1],
                    "transit_leg": arr_leg_payload
                })
                current_clock = max(current_clock, hotel_arr)
            else:
                day_plan.append({
                    "type": "attraction", "id": f"start_hotel_{day_idx}", "name": "Start Day at Hotel", "bucket": "logistics",
                    "start_time": current_clock.strftime("%H:%M"), "end_time": (current_clock + timedelta(minutes=5)).strftime("%H:%M"),
                    "transit_mins": 0, "unknown_hours_warning": False, "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1]
                })
                current_clock += timedelta(minutes=5)

            # 2. EVALUATE SEQUENTIAL ATTRACTIONS CANVAS
            active_time_spent = 0
            
            for poi_id in day_poi_ids:
                if isinstance(poi_id, str) and (poi_id.startswith("start_") or poi_id.startswith("return_") or poi_id.startswith("arr_") or poi_id.startswith("dep_")):
                    continue
                    
                p = poi_map.get(poi_id)
                if not p: continue
                
                # Auto-inject Lunch Check
                if current_clock.hour >= 13 and not lunch_taken:
                    day_plan.append({
                        "type": "meal", "name": "Lunch Break",
                        "start_time": current_clock.strftime("%H:%M"), "end_time": (current_clock + timedelta(minutes=self.lunch_duration_mins)).strftime("%H:%M")
                    })
                    current_clock += timedelta(minutes=self.lunch_duration_mins)
                    lunch_taken = True
                
                # ADAPTIVE COUPLING WATERFALL
                leg_key = f"{current_loc[0]:.5f},{current_loc[1]:.5f}->{p['latitude']:.5f},{p['longitude']:.5f}"
                
                # Look for verified route data matching our layout string key contract
                if leg_key in transit_lookup:
                    leg_meta = transit_lookup[leg_key]
                    active_mode = leg_meta.get("active_mode", "transit")
                    mode_bundle = leg_meta.get("alternatives", {}).get(active_mode, {})
                    
                    # Pull real duration and assign standard target logistics padding buffers (+5 mins)
                    raw_transit = mode_bundle.get("duration_mins", 15)
                    logistics_buffer = 5 if active_mode in ["transit", "uber", "driving"] else 0
                    final_transit_mins = raw_transit + logistics_buffer
                    
                    transit_leg_state = {
                        "is_verified": True,
                        "mode": active_mode,
                        "polyline": mode_bundle.get("polyline"),
                        "steps": mode_bundle.get("steps", []),
                        "distance_text": mode_bundle.get("distance_text", "")
                    }
                else:
                    # Cache Miss (Fallback to local haversine geometric estimation)
                    final_transit_mins = self._get_base_transit_mins(current_loc[0], current_loc[1], p['latitude'], p['longitude'])
                    transit_leg_state = {
                        "is_verified": False,
                        "mode": "estimated",
                        "polyline": None,
                        "steps": [],
                        "distance_text": ""
                    }

                arr_dt = current_clock + timedelta(minutes=final_transit_mins)
                raw_dur = p.get('recommended_duration_mins', 120)
                dep_dt = arr_dt + timedelta(minutes=raw_dur)
                
                is_open, is_unk = self._is_open_interval(arr_dt, dep_dt, p.get("opening_hours"))
                
                day_plan.append({
                    "type": "attraction", "id": p['id'], "name": p['name'], "bucket": p.get('bucket', 'want').lower(),
                    "start_time": arr_dt.strftime("%H:%M"), "end_time": dep_dt.strftime("%H:%M"),
                    "transit_mins": final_transit_mins, 
                    "unknown_hours_warning": not is_open if not is_unk else True,
                    "latitude": p['latitude'], "longitude": p['longitude'], "image_url": p.get('image_url'),
                    "transit_leg": transit_leg_state # Pass rich metadata block back to state
                })
                
                current_clock = dep_dt
                current_loc = (p['latitude'], p['longitude'])
                active_time_spent += 1
                
            # 3. INJECT RETURN ANCHORS WITH ROUTE SELECTION
            if active_time_spent > 0 or day_idx == 0:
                ret_key = f"{current_loc[0]:.5f},{current_loc[1]:.5f}->{self.hotel_coords[0]:.5f},{self.hotel_coords[1]:.5f}"
                return_transit_mins = self._get_base_transit_mins(current_loc[0], current_loc[1], self.hotel_coords[0], self.hotel_coords[1])
                ret_leg_payload = {"is_verified": False, "mode": "estimated", "polyline": None, "steps": []}
                
                if ret_key in transit_lookup:
                    active_mode = transit_lookup[ret_key].get("active_mode", "transit")
                    mode_data = transit_lookup[ret_key].get("alternatives", {}).get(active_mode, {})
                    return_transit_mins = mode_data.get("duration_mins", return_transit_mins) + 5
                    ret_leg_payload = {"is_verified": True, "mode": active_mode, "polyline": mode_data.get("polyline"), "steps": mode_data.get("steps", [])}

                return_dt = current_clock + timedelta(minutes=return_transit_mins)
                day_plan.append({
                    "type": "attraction", "id": f"return_hotel_{day_idx}", "name": "Return to Hotel", "bucket": "logistics",
                    "start_time": current_clock.strftime("%H:%M"), "end_time": return_dt.strftime("%H:%M"),
                    "transit_mins": return_transit_mins, "unknown_hours_warning": False,
                    "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1],
                    "transit_leg": ret_leg_payload
                })
                current_clock = return_dt
                
            if day_idx == total_days - 1:
                leave_for_airport_time = self.departure_dt - timedelta(hours=3)
                if current_clock < leave_for_airport_time:
                    day_plan.append({
                        "type": "free_time", "id": "free_time_hotel", "name": "Relax at Hotel / Grab Bags",
                        "start_time": current_clock.strftime("%H:%M"), "end_time": leave_for_airport_time.strftime("%H:%M")
                    })
                
                dep_key = f"{self.hotel_coords[0]:.5f},{self.hotel_coords[1]:.5f}->{self.airport_coords[0]:.5f},{self.airport_coords[1]:.5f}"
                airport_transit_mins = 60
                dep_leg_payload = {"is_verified": False, "mode": "estimated", "polyline": None, "steps": []}
                
                if dep_key in transit_lookup:
                    active_mode = transit_lookup[dep_key].get("active_mode", "driving")
                    mode_data = transit_lookup[dep_key].get("alternatives", {}).get(active_mode, {})
                    airport_transit_mins = mode_data.get("duration_mins", 60) + 5
                    dep_leg_payload = {"is_verified": True, "mode": active_mode, "polyline": mode_data.get("polyline"), "steps": mode_data.get("steps", [])}

                day_plan.append({
                    "type": "attraction", "id": "dep_airport", "name": "Transit to Airport & Depart", "bucket": "logistics",
                    "start_time": leave_for_airport_time.strftime("%H:%M"), "end_time": self.departure_dt.strftime("%H:%M"),
                    "transit_mins": airport_transit_mins, "unknown_hours_warning": False,
                    "latitude": self.airport_coords[0], "longitude": self.airport_coords[1],
                    "transit_leg": dep_leg_payload
                })
                
            schedule.append({"day_index": day_idx, "date": current_date.strftime("%Y-%m-%d"), "events": day_plan})

        # Calculate excluded pool
        assigned_ids = {pid for day_list in user_days_poi_ids for pid in day_list if isinstance(pid, int) or str(pid).isdigit()}
        excluded = {"must": [], "want": [], "optional": []}
        for p in pois:
            if p['id'] not in assigned_ids:
                bucket = p.get('bucket', 'optional').lower()
                if bucket not in excluded: bucket = "optional"
                excluded[bucket].append({"id": p["id"], "name": p["name"], "bucket": bucket, "type": "attraction"})

        return {"status": "success", "schedule": schedule, "excluded": excluded}

# ==========================================
# TEST HARNESS
# ==========================================
if __name__ == "__main__":
    arrival = datetime(2026, 6, 22, 9, 0)
    departure = datetime(2026, 6, 28, 9, 40)
    airport_coords = (41.8045, 12.2508)
    hotel_coords = (41.8255320603927, 12.4786448478699)

    engine = ScheduleEngine(
        pace="moderate", 
        arrival_dt=arrival, departure_dt=departure,
        hotel_coords=hotel_coords, airport_coords=airport_coords,
        wakeup_time="08:00", lunch_duration_mins=90
    )

    pois = [
        {"id": 60, "name": "Colosseum", "bucket": "must", "latitude": 41.890262, "longitude": 12.493086, "recommended_duration_mins": 90, "opening_hours": '{"monday": "08:30-16:30", "tuesday": "08:30-16:30", "wednesday": "08:30-16:30", "thursday": "08:30-16:30", "friday": "08:30-16:30", "saturday": "08:30-16:30", "sunday": "08:30-16:30"}'},
        {"id": 61, "name": "Roman Forum", "bucket": "must", "latitude": 41.891723, "longitude": 12.486671, "recommended_duration_mins": 120, "opening_hours": '{"monday": "09:00-19:15", "tuesday": "09:00-19:15", "wednesday": "09:00-19:15", "thursday": "09:00-19:15", "friday": "09:00-19:15", "saturday": "09:00-19:15", "sunday": "09:00-19:15"}'},
        {"id": 66, "name": "Vatican Museums", "bucket": "must", "latitude": 41.904960, "longitude": 12.454661, "recommended_duration_mins": 180, "opening_hours": '{"monday": "08:00-20:00", "tuesday": "08:00-20:00", "wednesday": "08:00-20:00", "thursday": "08:00-20:00", "friday": "08:00-20:00", "saturday": "08:00-20:00", "sunday": "Closed"}'},
        {"id": 63, "name": "Trevi Fountain", "bucket": "want", "latitude": 41.900978, "longitude": 12.483284, "recommended_duration_mins": 60, "opening_hours": '{"monday": "24/7", "tuesday": "24/7", "wednesday": "24/7", "thursday": "24/7", "friday": "24/7", "saturday": "24/7", "sunday": "24/7"}'},
        {"id": 64, "name": "Spanish Steps", "bucket": "want", "latitude": 41.906051, "longitude": 12.482872, "recommended_duration_mins": 90, "opening_hours": '{"monday": "00:00-24:00", "tuesday": "00:00-24:00", "wednesday": "00:00-24:00", "thursday": "00:00-24:00", "friday": "00:00-24:00", "saturday": "00:00-24:00", "sunday": "00:00-24:00"}'},
        {"id": 67, "name": "Sistine Chapel", "bucket": "must", "latitude": 41.902935, "longitude": 12.454403, "recommended_duration_mins": 120, "opening_hours": '{"monday": null, "tuesday": null, "wednesday": null, "thursday": null, "friday": null, "saturday": null, "sunday": "Closed"}'},
        {"id": 69, "name": "Capitoline Museums", "bucket": "want", "latitude": 41.892669, "longitude": 12.482208, "recommended_duration_mins": 180, "opening_hours": '{"monday": "09:30-19:30", "tuesday": "09:30-19:30", "wednesday": "09:30-19:30", "thursday": "09:30-19:30", "friday": "09:30-19:30", "saturday": "09:30-19:30", "sunday": "09:30-19:30"}'},
        {"id": 62, "name": "Palatine Hill", "bucket": "optional", "latitude": 41.889305, "longitude": 12.487109, "recommended_duration_mins": 180, "opening_hours": '{"monday": "09:00-19:15", "tuesday": "09:00-19:15", "wednesday": "09:00-19:15", "thursday": "09:00-19:15", "friday": "09:00-19:15", "saturday": "09:00-19:15", "sunday": "09:00-19:15"}'},
        {"id": 65, "name": "Basilica of St.Clement", "bucket": "optional", "latitude": 41.889312, "longitude": 12.497466, "recommended_duration_mins": 90, "opening_hours": '{"monday": null, "tuesday": null, "wednesday": null, "thursday": null, "friday": null, "saturday": null, "sunday": null}'},
        {"id": 68, "name": "Obelisk of Piazza Navona", "bucket": "optional", "latitude": 41.898956, "longitude": 12.473084, "recommended_duration_mins": 120, "opening_hours": '{"monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours", "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"}'},
        {"id": 70, "name": "Basilica di Santa Cecilia in Trastevere", "bucket": "optional", "latitude": 41.887561, "longitude": 12.475856, "recommended_duration_mins": 45, "opening_hours": '{"monday": "09:15-18:00", "tuesday": "09:15-18:00", "wednesday": "09:15-18:00", "thursday": "09:15-18:00", "friday": "09:15-18:00", "saturday": "09:15-18:00", "sunday": "09:15-18:00"}'},
        # FLORENCE ATTRACTIONS
        {"id": 48, "name": "Uffizi Gallery", "bucket": "must", "latitude": 43.768089, "longitude": 11.255364, "recommended_duration_mins": 180, "opening_hours": '{"monday": "Closed", "tuesday": "08:15-18:30", "wednesday": "08:15-18:30", "thursday": "08:15-18:30", "friday": "08:15-18:30", "saturday": "08:15-18:30", "sunday": "08:15-18:30"}'},
        {"id": 49, "name": "Ponte Vecchio", "bucket": "want", "latitude": 43.768421, "longitude": 11.253443, "recommended_duration_mins": 90, "opening_hours": '{"monday": "00:00-24:00", "tuesday": "00:00-24:00", "wednesday": "00:00-24:00", "thursday": "00:00-24:00", "friday": "00:00-24:00", "saturday": "00:00-24:00", "sunday": "00:00-24:00"}'},
        {"id": 50,"name": "Conservatorio Cherubini","bucket": "optional", "latitude": 43.776523, "longitude": 11.258512, "recommended_duration_mins": 120, "opening_hours": '{"monday": "Closed", "tuesday": "08:15-18:50", "wednesday": "08:15-18:50", "thursday": "08:15-18:50", "friday": "08:15-18:50", "saturday": "08:15-18:50", "sunday": "08:15-18:50"}'},
    ]

    print("\n--- RUNNING SCORING OPTIMIZER ---")
    result = engine.generate_schedule(pois)

    for day in result['schedule']:
        print(f"\nDAY {day['day_index'] + 1} - {day['date']}")
        for event in day['events']:
            if event['type'] == 'meal':
                print(f"  [{event['start_time']} - {event['end_time']}] 🍔 {event['name']}")
            elif event['type'] == 'free_time':
                print(f"  [{event['start_time']} - {event['end_time']}] ☕ {event['name']}")
            else:
                warn_str = " ⚠️ (Unknown Hours)" if event.get('unknown_hours_warning') else ""
                t_str = f"(Transit: {event['transit_mins']}m) -> "
                print(f"  {t_str}[{event['start_time']} - {event['end_time']}] ⭐ {event['name']} ({event['bucket'].upper()}){warn_str}")

    print("\n" + "="*50)
    print("DROPPED ATTRACTIONS:")
    excluded = result['excluded']
    for bucket in ['must', 'want', 'optional']:
        if excluded[bucket]:
            print(f"  - {bucket.upper()}: {', '.join(excluded[bucket])}")
        else:
            print(f"  - {bucket.upper()}: None dropped! 🎉")
import math
from datetime import datetime, timedelta, time
from typing import List, Dict, Any
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

class ScheduleEngine:
    def __init__(self, pace: str, arrival_dt: datetime, departure_dt: datetime, 
                 hotel_coords: tuple, airport_coords: tuple,
                 wakeup_time: str = "08:00", lunch_duration_mins: int = 90):
        
        self.pace = pace.lower()
        self.arrival_dt = arrival_dt
        self.departure_dt = departure_dt
        self.hotel_coords = hotel_coords
        self.lunch_duration_mins = lunch_duration_mins
        self.arrival_buffer_hours = 3.5 
        
        wakeup_t = datetime.strptime(wakeup_time, "%H:%M").time()
        self.morning_start_delta = timedelta(hours=wakeup_t.hour, minutes=wakeup_t.minute) + timedelta(minutes=90)
        
        self.priority_weights = {"must-see": 3, "want-to-see": 2, "optional": 1}
        
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
            hours_dict = json.loads(opening_hours_str)
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
        except Exception:
            return True, True 
        return True, False

    def _score_poi(self, poi: dict, current_loc: tuple, active_time: int, soft_budget: int, hard_budget: int, eff_cost: int) -> float:
        """
        The Unified Scoring Model.
        Balances Priority, Geographic proximity, and Budget Constraints.
        """
        # 1. Base Priority Score
        score = poi['priority_score'] * 1000 
        
        # 2. Distance Penalty (Prevents zig-zagging)
        dist = self._calculate_distance_degrees(current_loc[0], current_loc[1], poi['latitude'], poi['longitude'])
        score -= (dist * 500)
        
        # 3. Constraint Pressure
        # If adding this item pushes us over the Soft Budget, heavily penalize it unless it is a MUST-SEE.
        if active_time + eff_cost > soft_budget:
            if poi['bucket'] != 'must-see':
                score -= 5000 # Effectively bans it, stopping early to create slack
            else:
                score -= 500  # Allowed, but lightly penalized to indicate stress
                
        return score

    def generate_schedule(self, pois: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not pois: return {"status": "success", "schedule": [], "excluded": {}}
        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        
        for p in pois:
            p['bucket'] = p.get('bucket', 'want-to-see').lower()
            p['priority_score'] = self.priority_weights.get(p['bucket'], 2)

        # --- MACRO REGION CLASSIFICATION ---
        # Instead of K-Means, simply identify POIs that are far from the hotel (> 0.5 degrees, ~55km)
        home_pois = []
        excursion_pois = []
        for p in pois:
            if self._calculate_distance_degrees(self.hotel_coords[0], self.hotel_coords[1], p['latitude'], p['longitude']) > 0.5:
                excursion_pois.append(p)
            else:
                home_pois.append(p)

        # --- DAY ALLOCATION ---
        active_days = []
        for i in range(total_days):
            h_arr = self.arrival_dt + timedelta(hours=self.arrival_buffer_hours)
            if i == 0 and h_arr >= self.arrival_dt.replace(hour=self.hard_day_cutoff.hour, minute=self.hard_day_cutoff.minute): continue
            if i == total_days - 1 and (self.departure_dt - timedelta(hours=3)) <= self.departure_dt.replace(hour=9, minute=0): continue
            active_days.append(i)

        if not active_days: return {"status": "error"}

        available_days = list(active_days)
        excursion_day_map = {}
        
        # Assign excursion days (e.g., Florence gets the middle day of the trip)
        if excursion_pois and len(available_days) > 1:
            excursion_day_idx = available_days.pop(len(available_days) // 2)
            excursion_day_map[excursion_day_idx] = excursion_pois
            
        home_days = available_days
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
            
            # Start Clock
            if day_idx == 0:
                current_clock = max(self.arrival_dt + timedelta(hours=self.arrival_buffer_hours), 
                                  datetime.combine(current_date, time()) + self.morning_start_delta)
            else:
                current_clock = datetime.combine(current_date, time()) + self.morning_start_delta
            
            end_clk = (self.departure_dt - timedelta(hours=3)) if day_idx == total_days - 1 else datetime.combine(current_date, self.hard_day_cutoff)

            current_loc = self.hotel_coords
            active_time_spent = 0
            lunch_taken = False
            day_plan = []
            
            # Isolate the POI pool for the day's mode
            daily_pool = excursion_day_map[day_idx] if is_excursion else [p for p in unassigned_pois if p in home_pois]
            
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
                    raw_transit = self._get_base_transit_mins(current_loc[0], current_loc[1], p['latitude'], p['longitude'])
                    
                    eff_total, eff_transit, switch_pen = self._get_effective_costs(raw_dur, raw_transit, rigidity)
                    
                    arr_dt = current_clock + timedelta(minutes=eff_transit)
                    
                    # Wait Mechanic
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
                            "wait": wait_mins, "eff_total": eff_total, "unk": is_unk, "raw_transit": raw_transit
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
                    "transit_mins": best_candidate['raw_transit'], "unknown_hours_warning": best_candidate['unk']
                })
                
                current_clock = best_candidate['dep']
                current_loc = (b_poi['latitude'], b_poi['longitude'])
                active_time_spent += best_candidate['eff_total']
                
                daily_pool = [p for p in daily_pool if p['id'] != b_poi['id']]
                unassigned_pois = [p for p in unassigned_pois if p['id'] != b_poi['id']]

            if day_plan:
                schedule.append({"day_index": day_idx, "date": current_date.strftime("%Y-%m-%d"), "events": day_plan})

        # --- EXCLUDED ---
        excluded = {"must-see": [], "want-to-see": [], "optional": []}
        for p in unassigned_pois: excluded[p['bucket']].append(p['name'])

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
        {"id": 60, "name": "Colosseum", "bucket": "must-see", "latitude": 41.890262, "longitude": 12.493086, "recommended_duration_mins": 90, "opening_hours": '{"monday": "08:30-16:30", "tuesday": "08:30-16:30", "wednesday": "08:30-16:30", "thursday": "08:30-16:30", "friday": "08:30-16:30", "saturday": "08:30-16:30", "sunday": "08:30-16:30"}'},
        {"id": 61, "name": "Roman Forum", "bucket": "must-see", "latitude": 41.891723, "longitude": 12.486671, "recommended_duration_mins": 120, "opening_hours": '{"monday": "09:00-19:15", "tuesday": "09:00-19:15", "wednesday": "09:00-19:15", "thursday": "09:00-19:15", "friday": "09:00-19:15", "saturday": "09:00-19:15", "sunday": "09:00-19:15"}'},
        {"id": 66, "name": "Vatican Museums", "bucket": "must-see", "latitude": 41.904960, "longitude": 12.454661, "recommended_duration_mins": 180, "opening_hours": '{"monday": "08:00-20:00", "tuesday": "08:00-20:00", "wednesday": "08:00-20:00", "thursday": "08:00-20:00", "friday": "08:00-20:00", "saturday": "08:00-20:00", "sunday": "Closed"}'},
        {"id": 63, "name": "Trevi Fountain", "bucket": "want-to-see", "latitude": 41.900978, "longitude": 12.483284, "recommended_duration_mins": 60, "opening_hours": '{"monday": "24/7", "tuesday": "24/7", "wednesday": "24/7", "thursday": "24/7", "friday": "24/7", "saturday": "24/7", "sunday": "24/7"}'},
        {"id": 64, "name": "Spanish Steps", "bucket": "want-to-see", "latitude": 41.906051, "longitude": 12.482872, "recommended_duration_mins": 90, "opening_hours": '{"monday": "00:00-24:00", "tuesday": "00:00-24:00", "wednesday": "00:00-24:00", "thursday": "00:00-24:00", "friday": "00:00-24:00", "saturday": "00:00-24:00", "sunday": "00:00-24:00"}'},
        {"id": 67, "name": "Sistine Chapel", "bucket": "must-see", "latitude": 41.902935, "longitude": 12.454403, "recommended_duration_mins": 120, "opening_hours": '{"monday": null, "tuesday": null, "wednesday": null, "thursday": null, "friday": null, "saturday": null, "sunday": "Closed"}'},
        {"id": 69, "name": "Capitoline Museums", "bucket": "want-to-see", "latitude": 41.892669, "longitude": 12.482208, "recommended_duration_mins": 180, "opening_hours": '{"monday": "09:30-19:30", "tuesday": "09:30-19:30", "wednesday": "09:30-19:30", "thursday": "09:30-19:30", "friday": "09:30-19:30", "saturday": "09:30-19:30", "sunday": "09:30-19:30"}'},
        {"id": 62, "name": "Palatine Hill", "bucket": "optional", "latitude": 41.889305, "longitude": 12.487109, "recommended_duration_mins": 180, "opening_hours": '{"monday": "09:00-19:15", "tuesday": "09:00-19:15", "wednesday": "09:00-19:15", "thursday": "09:00-19:15", "friday": "09:00-19:15", "saturday": "09:00-19:15", "sunday": "09:00-19:15"}'},
        {"id": 65, "name": "Basilica of St.Clement", "bucket": "optional", "latitude": 41.889312, "longitude": 12.497466, "recommended_duration_mins": 90, "opening_hours": '{"monday": null, "tuesday": null, "wednesday": null, "thursday": null, "friday": null, "saturday": null, "sunday": null}'},
        {"id": 68, "name": "Obelisk of Piazza Navona", "bucket": "optional", "latitude": 41.898956, "longitude": 12.473084, "recommended_duration_mins": 120, "opening_hours": '{"monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours", "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"}'},
        {"id": 70, "name": "Basilica di Santa Cecilia in Trastevere", "bucket": "optional", "latitude": 41.887561, "longitude": 12.475856, "recommended_duration_mins": 45, "opening_hours": '{"monday": "09:15-18:00", "tuesday": "09:15-18:00", "wednesday": "09:15-18:00", "thursday": "09:15-18:00", "friday": "09:15-18:00", "saturday": "09:15-18:00", "sunday": "09:15-18:00"}'},
        # FLORENCE ATTRACTIONS
        {"id": 48, "name": "Uffizi Gallery", "bucket": "must-see", "latitude": 43.768089, "longitude": 11.255364, "recommended_duration_mins": 180, "opening_hours": '{"monday": "Closed", "tuesday": "08:15-18:30", "wednesday": "08:15-18:30", "thursday": "08:15-18:30", "friday": "08:15-18:30", "saturday": "08:15-18:30", "sunday": "08:15-18:30"}'},
        {"id": 49, "name": "Ponte Vecchio", "bucket": "want-to-see", "latitude": 43.768421, "longitude": 11.253443, "recommended_duration_mins": 90, "opening_hours": '{"monday": "00:00-24:00", "tuesday": "00:00-24:00", "wednesday": "00:00-24:00", "thursday": "00:00-24:00", "friday": "00:00-24:00", "saturday": "00:00-24:00", "sunday": "00:00-24:00"}'},
        {"id": 50, "name": "Conservatorio Cherubini", "bucket": "optional", "latitude": 43.776523, "longitude": 11.258512, "recommended_duration_mins": 120, "opening_hours": '{"monday": "Closed", "tuesday": "08:15-18:50", "wednesday": "08:15-18:50", "thursday": "08:15-18:50", "friday": "08:15-18:50", "saturday": "08:15-18:50", "sunday": "08:15-18:50"}'},
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
    for bucket in ['must-see', 'want-to-see', 'optional']:
        if excluded[bucket]:
            print(f"  - {bucket.upper()}: {', '.join(excluded[bucket])}")
        else:
            print(f"  - {bucket.upper()}: None dropped! 🎉")
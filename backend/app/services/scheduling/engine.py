import numpy as np
from sklearn.cluster import KMeans
from datetime import datetime, timedelta, time
from typing import List, Dict, Any
import logging
import json
import math

# Setup basic logging
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
        self.pace_mapping = {"relaxed": 5 * 60, "moderate": 7 * 60, "fast-paced": 9 * 60}
        
        self.daily_active_budget = self.pace_mapping.get(self.pace, 7 * 60)
        self.hard_day_cutoff = time(20, 0) # 8:00 PM
        
        # Base walking/transit padding between nearby places
        self.base_padding_mins = 30

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        return (lat1 - lat2)**2 + (lon1 - lon2)**2

    def _estimate_transit_mins(self, lat1, lon1, lat2, lon2):
        """
        Heuristic: 1 coordinate degree is ~111km. 
        Calculates realistic travel times including high-speed inter-city transit.
        """
        dist_degrees = math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
        added_transit = int(dist_degrees * 70) 
        return self.base_padding_mins + added_transit

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
                
                if open_t <= close_t:
                    return (open_t <= arr_t and dep_t <= close_t), False
                else:
                    return (arr_t >= open_t or dep_t <= close_t), False
        except Exception:
            return True, True 
        return True, False

    def _attempt_insert(self, poi: dict, day_state: dict) -> bool:
        """
        Tries to insert a single POI into a specific day's timeline.
        Includes the "Wait/Coffee" mechanic if opening hours are slightly off.
        """
        current_clock = day_state['current_clock']
        current_loc = day_state['current_loc']
        
        # 1. Meal Check
        lunch_added_time = 0
        if current_clock.hour >= 13 and not day_state['lunch_taken']:
            lunch_added_time = self.lunch_duration_mins
            
        # 2. Transit Check
        transit_mins = self._estimate_transit_mins(current_loc[0], current_loc[1], poi['latitude'], poi['longitude'])
        base_arr_dt = current_clock + timedelta(minutes=lunch_added_time + transit_mins)
        duration = poi.get('recommended_duration_mins', 120)
        
        # 3. The "Wait" Mechanic (Try arrival times in 30 min increments up to 1.5 hrs)
        wait_mins = 0
        best_arr_dt = None
        best_dep_dt = None
        is_unk = False
        
        while wait_mins <= 90:
            test_arr = base_arr_dt + timedelta(minutes=wait_mins)
            test_dep = test_arr + timedelta(minutes=duration)
            
            # Constraints
            if test_dep > day_state['hard_cutoff_dt']: break
            if day_state['active_time'] + duration > self.daily_active_budget: break
                
            is_open, unk = self._is_open_interval(test_arr, test_dep, poi.get("opening_hours"))
            if is_open:
                best_arr_dt = test_arr
                best_dep_dt = test_dep
                is_unk = unk
                break
                
            wait_mins += 30
            
        if not best_arr_dt: return False # Failed all checks
        
        # 4. Commit to State
        if lunch_added_time > 0:
            lunch_start = current_clock
            lunch_end = current_clock + timedelta(minutes=lunch_added_time)
            day_state['events'].append({
                "type": "meal", "name": "Lunch Break", 
                "start_time": lunch_start.strftime("%H:%M"), "end_time": lunch_end.strftime("%H:%M")
            })
            day_state['lunch_taken'] = True
            
        if wait_mins > 0:
            wait_start = base_arr_dt
            wait_end = base_arr_dt + timedelta(minutes=wait_mins)
            day_state['events'].append({
                "type": "free_time", "name": "Free Time / Wait for Opening", 
                "start_time": wait_start.strftime("%H:%M"), "end_time": wait_end.strftime("%H:%M")
            })

        day_state['events'].append({
            "type": "attraction",
            "id": poi['id'], "name": poi['name'], "bucket": poi['bucket'],
            "start_time": best_arr_dt.strftime("%H:%M"), "end_time": best_dep_dt.strftime("%H:%M"),
            "transit_mins": transit_mins, "unknown_hours_warning": is_unk
        })
        
        day_state['current_clock'] = best_dep_dt
        day_state['current_loc'] = (poi['latitude'], poi['longitude'])
        day_state['active_time'] += duration
        return True

    def generate_schedule(self, pois: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not pois: return {"status": "success", "schedule": [], "excluded": {}}
        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        
        for p in pois:
            p['bucket'] = p.get('bucket', 'want-to-see').lower()
            p['priority_score'] = self.priority_weights.get(p['bucket'], 2)

        # --- PHASE 1: MACRO REGIONS (City Partitioning) ---
        regions = []
        for p in pois:
            placed = False
            for r in regions:
                if self._calculate_distance(p['latitude'], p['longitude'], r['center'][0], r['center'][1]) < 0.5:
                    r['pois'].append(p)
                    placed = True
                    break
            if not placed:
                regions.append({'center': (p['latitude'], p['longitude']), 'pois': [p], 'is_base': False})
                
        # Identify Base Region
        base_region = None
        for r in regions:
            if self._calculate_distance(r['center'][0], r['center'][1], self.hotel_coords[0], self.hotel_coords[1]) < 0.5:
                r['is_base'] = True
                base_region = r
                break
        
        if not base_region:
            # Fallback if hotel is miles away from everything
            base_region = regions[0]
            base_region['is_base'] = True

        # --- PHASE 2: DAY ALLOCATION ---
        budgets = [self.daily_active_budget] * total_days
        hotel_arr = self.arrival_dt + timedelta(hours=self.arrival_buffer_hours)
        if hotel_arr >= self.arrival_dt.replace(hour=self.hard_day_cutoff.hour, minute=self.hard_day_cutoff.minute): budgets[0] = 0
        if (self.departure_dt - timedelta(hours=3)) <= self.departure_dt.replace(hour=9, minute=0): budgets[-1] = 0

        active_days = [i for i, b in enumerate(budgets) if b > 0]
        if not active_days: return {"status": "error"}

        day_assignments = {}
        available_days = list(active_days)
        
        # Give 1 Day to each Day Trip (Middle days preferred)
        day_trip_regions = [r for r in regions if not r['is_base']]
        for r in day_trip_regions:
            if len(available_days) > 1:
                assigned = available_days.pop(len(available_days) // 2)
                r['assigned_days'] = [assigned]
            else:
                r['assigned_days'] = [] # Out of days!
                
        base_region['assigned_days'] = available_days

        # --- PHASE 3: MICRO NEIGHBORHOODS (Base City Only) ---
        if len(base_region['assigned_days']) > 0 and len(base_region['pois']) > 0:
            n_clusters = min(len(base_region['assigned_days']), len(base_region['pois']))
            coords = np.array([[p['latitude'], p['longitude']] for p in base_region['pois']])
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto').fit(coords)
            
            for i, p in enumerate(base_region['pois']):
                p['target_day'] = base_region['assigned_days'][int(kmeans.labels_[i])]
                p['region'] = base_region

        for r in day_trip_regions:
            for p in r['pois']:
                p['target_day'] = r['assigned_days'][0] if r['assigned_days'] else None
                p['region'] = r

        # Initialize Daily States
        day_states = {}
        for d in active_days:
            c_date = self.arrival_dt.date() + timedelta(days=d)
            start_clk = max(hotel_arr, datetime.combine(c_date, time()) + self.morning_start_delta) if d == 0 else datetime.combine(c_date, time()) + self.morning_start_delta
            end_clk = (self.departure_dt - timedelta(hours=3)) if d == total_days - 1 else datetime.combine(c_date, self.hard_day_cutoff)
            
            day_states[d] = {
                "day_idx": d, "date": c_date.strftime("%Y-%m-%d"),
                "current_clock": start_clk, "current_loc": self.hotel_coords,
                "active_time": 0, "lunch_taken": False, "events": [],
                "hard_cutoff_dt": end_clk
            }

        leftovers = []

        # --- PASS 1: Strict Neighborhood Insertion ---
        for p in pois:
            target = p.get('target_day')
            if target is None:
                leftovers.append(p)
                continue
                
            # If it fails its target day, it goes to leftovers
            if not self._attempt_insert(p, day_states[target]):
                leftovers.append(p)

        # --- PASS 2: The Global Rescue (Priority-Driven) ---
        leftovers.sort(key=lambda x: -x['priority_score']) # Save Must-Sees First!
        excluded_pois = []
        
        for p in leftovers:
            saved = False
            # Only try to rescue within its assigned Macro-Region
            valid_days = p['region']['assigned_days']
            for d in valid_days:
                if self._attempt_insert(p, day_states[d]):
                    saved = True
                    break
            if not saved:
                excluded_pois.append(p)

        # Final Formatting
        schedule = []
        for d in active_days:
            if day_states[d]['events']:
                schedule.append({"day_index": d, "date": day_states[d]['date'], "events": day_states[d]['events']})

        excluded = {"must-see": [], "want-to-see": [], "optional": []}
        for p in excluded_pois: excluded[p['bucket']].append(p['name'])

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

    print("\n--- RUNNING THE MULTI-PASS HYBRID SCHEDULER ---")
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
import math
import json
import numpy as np
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional

from sklearn.cluster import KMeans
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from app.core.logger import get_logger
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
        self.airport_egress_mins = 90
        self.hotel_checkin_mins = 45
        self.pre_flight_buffer_mins = 180

        wakeup_t = datetime.strptime(wakeup_time, "%H:%M").time()
        self.wakeup_delta = timedelta(hours=wakeup_t.hour, minutes=wakeup_t.minute)

        self.priority_weights = {"must": 100000, "want": 25000, "optional": 10000}

        self.pace_profiles = {
            "relaxed": {"end_time": time(18, 30)},
            "moderate": {"end_time": time(20, 30)},
            "fast-paced": {"end_time": time(22, 30)}
        }
        
    def _get_real_distance_km(self, lat1, lon1, lat2, lon2):
        R = 6371.0 
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _get_base_transit_mins(self, lat1, lon1, lat2, lon2):
        straight_dist = self._get_real_distance_km(lat1, lon1, lat2, lon2)
        if straight_dist < 0.1: return 2 

        if straight_dist < 1.0:
            dist_km = straight_dist * 1.35
            return 2 + int((dist_km / 4.0) * 60)

        straight_dist -= 1.0

        if straight_dist < 19.0:
            dist_km = straight_dist * 1.35
            return 5 + int((1.35 / 4.0) * 60) + int((dist_km / 25.0) * 60)

        straight_dist -= 19.0
        return 15 + int((1.35 / 4.0) * 60) + int((25.65 / 25.0) * 60) + int((straight_dist / 130.0) * 60)


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
                "is_verified": True, "mode": active_mode, "polyline": mode_bundle.get("polyline"),
                "steps": mode_bundle.get("steps", []), "distance_text": mode_bundle.get("distance_text", ""),
                "alternatives": leg_meta.get("alternatives")
            }
        return default_mins, {
            "is_verified": False, "mode": "estimated", "polyline": None, "steps": [], "distance_text": ""
        }

    def _get_time_window(self, opening_hours_str: Any, date_obj: datetime, duration_mins: int) -> Optional[tuple[int, int]]:
        fallback = (0, 1440 - duration_mins)
        if not opening_hours_str: return fallback 
        
        day_of_week = date_obj.strftime('%A').lower()
        try:
            if isinstance(opening_hours_str, bytes):
                opening_hours_str = opening_hours_str.decode('utf-8')
                
            if isinstance(opening_hours_str, str):
                hours_dict = json.loads(opening_hours_str)
            elif isinstance(opening_hours_str, dict):
                hours_dict = opening_hours_str
            else:
                return fallback

            day_hours = hours_dict.get(day_of_week)
            if day_hours is None or str(day_hours).lower() == "null": return fallback
            if "closed" in str(day_hours).lower(): return None
            if "24" in str(day_hours).lower() or "00:00-24:00" in str(day_hours): return fallback
            
            if "-" in str(day_hours):
                open_str, close_str = str(day_hours).split("-")
                open_t = datetime.strptime(open_str.strip(), "%H:%M").time()
                close_t = datetime.strptime(close_str.strip(), "%H:%M").time()
                
                open_min = open_t.hour * 60 + open_t.minute
                close_min = close_t.hour * 60 + close_t.minute
                
                max_start = close_min - duration_mins
                if max_start < open_min: 
                    return None 
                return (open_min, max_start)
                
        except Exception as e:
            log.warning(f"Failed to parse opening hours: {e} | Defaulting to Always Open.")
            
        return fallback

    def _cluster_pois(self, pois: List[Dict], k: int) -> Dict[int, List[Dict]]:
        if not pois or k <= 1: return {0: pois}
        if k >= len(pois): return {i: [p] for i, p in enumerate(pois)}
        
        coords = np.array([[p['latitude'], p['longitude']] for p in pois])
        kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(coords)
        
        clusters = {i: [] for i in range(k)}
        for i, label in enumerate(kmeans.labels_):
            clusters[label].append(pois[i])
            
        return clusters

    def _balance_clusters(
        self, 
        clusters: Dict[int, List[Dict]], 
        max_distance_km: float = 8.0,
        max_passes: int = 20,
        tolerance_mins: int = 30
    ) -> Dict[int, List[Dict]]:
        """
        Greedy load-balancing for K-Means clusters.

        Args:
            clusters:          Raw K-Means output {cluster_id: [poi, ...]}
            max_distance_km:   A POI will only be relocated if its straight-line
                               distance to the destination cluster's centroid is
                               at most this value.  Keeps geographic coherence.
            max_passes:        Safety cap on the outer while-loop.
            tolerance_mins:    Stop when the difference between the most-loaded
                               and least-loaded cluster is within this value.

        Returns:
            A new dict with the same structure but balanced duration loads.
        """
        if len(clusters) <= 1:
            return clusters

        balanced = {k: list(v) for k, v in clusters.items()}

        def _cluster_load(pois: List[Dict]) -> int:
            return sum(p.get('recommended_duration_mins', 120) for p in pois)

        def _centroid(pois: List[Dict]) -> tuple[float, float]:
            if not pois:
                return (0.0, 0.0)
            lats = [p['latitude'] for p in pois]
            lons = [p['longitude'] for p in pois]
            return (sum(lats) / len(lats), sum(lons) / len(lons))

        for _ in range(max_passes):
            loads = {k: _cluster_load(v) for k, v in balanced.items()}
            max_k = max(loads, key=loads.get)
            min_k = min(loads, key=loads.get)

            if loads[max_k] - loads[min_k] <= tolerance_mins:
                break

            if len(balanced[max_k]) < 2:
                break

            dest_centroid = _centroid(balanced[min_k])

            priority_order = {"optional": 0, "want": 1, "must": 2}
            candidates = [
                p for p in balanced[max_k]
                if p.get('bucket', 'want').lower() != 'must'
                and self._get_real_distance_km(
                    p['latitude'], p['longitude'],
                    dest_centroid[0], dest_centroid[1]
                ) <= max_distance_km
            ]

            if not candidates:
                break

            candidates.sort(key=lambda p: (
                priority_order.get(p.get('bucket', 'want').lower(), 1),
                self._get_real_distance_km(
                    p['latitude'], p['longitude'],
                    dest_centroid[0], dest_centroid[1]
                )
            ))

            poi_to_move = candidates[0]
            balanced[max_k].remove(poi_to_move)
            balanced[min_k].append(poi_to_move)

            log.debug(
                f"[balance_clusters] Moved '{poi_to_move['name']}' "
                f"({poi_to_move.get('recommended_duration_mins', 120)} min, "
                f"{poi_to_move.get('bucket', 'want')}) "
                f"from cluster {max_k} (load {loads[max_k]}) "
                f"to cluster {min_k} (load {loads[min_k]})"
            )

        return balanced

    def _solve_day_route(self, day_nodes: List[Dict], start_min: int, end_min: int, transit_lookup: dict):
        num_nodes = len(day_nodes)
        if num_nodes < 2: return []
        manager = pywrapcp.RoutingIndexManager(num_nodes, 1, [0], [num_nodes - 1])
        routing = pywrapcp.RoutingModel(manager)

        time_matrix = [[0] * num_nodes for _ in range(num_nodes)]
        
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    time_matrix[i][j] = 0
                    continue
                
                n1, n2 = day_nodes[i], day_nodes[j]
                
                if n1['type'] == 'meal' or n2['type'] == 'meal':
                    transit = 5
                else:
                    est_mins = self._get_base_transit_mins(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
                    transit, _ = self._resolve_transit_leg(n1['lat'], n1['lon'], n2['lat'], n2['lon'], transit_lookup, est_mins)
                
                time_matrix[i][j] = transit + n1['duration']
        
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return time_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        routing.AddDimension(
            transit_callback_index,
            180,  
            2880, 
            False, 
            "Time"
        )
        time_dimension = routing.GetDimensionOrDie("Time")

        safe_start = int(start_min)
        safe_end = int(max(start_min, end_min))
        
        start_index = routing.Start(0)
        time_dimension.CumulVar(start_index).SetRange(safe_start, safe_start)
        
        end_index = routing.End(0)
        time_dimension.CumulVar(end_index).SetRange(safe_start, safe_end)

        for i in range(1, num_nodes - 1):
            index = manager.NodeToIndex(i)
            node = day_nodes[i]
            
            poi_open = int(node['open_min'])
            poi_close = int(max(poi_open, node['max_start_min'])) 
            
            time_dimension.CumulVar(index).SetRange(poi_open, poi_close)
            routing.AddDisjunction([index], int(node['penalty']))
            
            if node['type'] == 'meal':
                ideal_lunch = int(safe_start + (5 * 60))
                time_dimension.SetCumulVarSoftLowerBound(index, ideal_lunch, 10)
                time_dimension.SetCumulVarSoftUpperBound(index, ideal_lunch, 10)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        search_parameters.time_limit.seconds = 2 

        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            log.warning("Solver failed to find a feasible solution.")
            return [] 

        route = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node_idx = manager.IndexToNode(index)
            arr_min = solution.Value(time_dimension.CumulVar(index))
            route.append({
                "node": day_nodes[node_idx],
                "arr_min": arr_min,
                "dep_min": arr_min + day_nodes[node_idx]['duration']
            })
            index = solution.Value(routing.NextVar(index))
            
        node_idx = manager.IndexToNode(index)
        arr_min = solution.Value(time_dimension.CumulVar(index))
        route.append({
            "node": day_nodes[node_idx], "arr_min": arr_min, "dep_min": arr_min
        })
        
        return route

    def generate_schedule(self, pois: List[Dict[str, Any]], 
                          existing_transit_legs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        if not pois: return {"status": "success", "schedule": [], "excluded": {}}
        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        transit_lookup = existing_transit_legs or {}

        home_pois, excursion_pois = [], []
        for p in pois:
            if self._get_real_distance_km(self.hotel_coords[0], self.hotel_coords[1], p['latitude'], p['longitude']) > 55:
                excursion_pois.append(p)
            else:
                home_pois.append(p)

        active_days = list(range(total_days))
        full_days = [i for i in active_days if i != 0 and i != total_days - 1]
        excursion_groups = []
        for p in excursion_pois:
            placed = False
            for group in excursion_groups:
                if self._get_real_distance_km(p['latitude'], p['longitude'], group[0]['latitude'], group[0]['longitude']) < 30:
                    group.append(p)
                    placed = True
                    break
            if not placed:
                excursion_groups.append([p])

        excursion_day_map = {}
        for i, group in enumerate(excursion_groups):
            if i < len(full_days):
                target_day = full_days[i * (len(full_days) // len(excursion_groups))]
                excursion_day_map[target_day] = group
            else:
                log.warning(f"More day trips ({len(excursion_groups)}) than available full days ({len(full_days)})!")

        home_days = [d for d in full_days if d not in excursion_day_map]
        k_clusters = len(home_days) if home_days else 1
        raw_clusters = self._cluster_pois(home_pois, k_clusters)
        balanced_clusters = self._balance_clusters(raw_clusters)

        day_cluster_hint: Dict[int, set] = {}
        for i, day_idx in enumerate(home_days):
            cluster_pois = balanced_clusters.get(i, [])
            day_cluster_hint[day_idx] = {p['id'] for p in cluster_pois}

        remaining_home_pois: List[Dict] = list(home_pois)

        schedule = []
        assigned_ids: set = set()

        profile = self.pace_profiles.get(self.pace, self.pace_profiles["moderate"])

        for day_idx in active_days:
            current_date = self.arrival_dt.date() + timedelta(days=day_idx)
            is_excursion = day_idx in excursion_day_map
            base_dt = datetime.combine(current_date, time.min)
            day_plan = []
            
            if day_idx == 0:
                wakeup_dt = datetime.combine(current_date, time()) + self.wakeup_delta
                ready_dt = wakeup_dt + timedelta(minutes=90)
                
                bags_claim_end = self.arrival_dt + timedelta(minutes=self.airport_egress_mins)
                day_plan.append({
                    "type": "attraction", "id": "arr_airport", "name": "Customs & Baggage Claim", "bucket": "logistics",
                    "start_time": self.arrival_dt.strftime("%H:%M"), "end_time": bags_claim_end.strftime("%H:%M"),
                    "transit_mins": 0, "unknown_hours_warning": False, "latitude": self.airport_coords[0], "longitude": self.airport_coords[1]
                })
                est_arr_mins = self._get_base_transit_mins(
                    self.airport_coords[0], self.airport_coords[1], 
                    self.hotel_coords[0], self.hotel_coords[1]
                )
                h_transit, h_leg = self._resolve_transit_leg(
                    self.airport_coords[0], self.airport_coords[1], 
                    self.hotel_coords[0], self.hotel_coords[1], 
                    transit_lookup, est_arr_mins
                )
                hotel_arrival_time = bags_claim_end + timedelta(minutes=h_transit)
                checkin_end_time = hotel_arrival_time + timedelta(minutes=self.hotel_checkin_mins)
                day_plan.append({
                    "type": "attraction", "id": "arr_hotel", "name": "Check-in & Settle at Hotel", "bucket": "logistics",
                    "start_time": hotel_arrival_time.strftime("%H:%M"), "end_time": checkin_end_time.strftime("%H:%M"),
                    "transit_mins": h_transit, "unknown_hours_warning": False, "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1], "transit_leg": h_leg
                })
                start_clk_dt = max(checkin_end_time, ready_dt)
                
                base_cutoff = profile["end_time"]
                early_cutoff_mins = min(base_cutoff.hour * 60 + base_cutoff.minute, 20 * 60)
                day_end_limit = datetime.combine(current_date, time(early_cutoff_mins // 60, early_cutoff_mins % 60))
                end_node_coords = self.hotel_coords
                
            elif day_idx == total_days - 1:
                wakeup_dt = datetime.combine(current_date, time()) + self.wakeup_delta
                ready_dt = wakeup_dt + timedelta(minutes=90)
                day_end_limit = self.departure_dt - timedelta(minutes=self.pre_flight_buffer_mins)
                
                est_dep_mins = self._get_base_transit_mins(
                    self.hotel_coords[0], self.hotel_coords[1], 
                    self.airport_coords[0], self.airport_coords[1]
                )
                dep_transit_mins, _ = self._resolve_transit_leg(
                    self.hotel_coords[0], self.hotel_coords[1], 
                    self.airport_coords[0], self.airport_coords[1], 
                    transit_lookup, est_dep_mins
                )
                
                latest_leave_time = day_end_limit - timedelta(minutes=dep_transit_mins)
                
                if ready_dt > latest_leave_time:
                    ready_dt = latest_leave_time
                    wakeup_dt = ready_dt - timedelta(minutes=90)
                
                start_clk_dt = ready_dt
                end_node_coords = self.airport_coords
                
            elif is_excursion:
                max_transit_mins = max([
                    self._get_base_transit_mins(self.hotel_coords[0], self.hotel_coords[1], p['latitude'], p['longitude']) 
                    for p in excursion_day_map[day_idx]
                ])
                
                ideal_wakeup = datetime.combine(current_date, time()) + self.wakeup_delta
                
                shift_mins = min(max_transit_mins, 120)
                dynamic_wakeup = ideal_wakeup - timedelta(minutes=shift_mins)
                
                earliest_allowed = datetime.combine(current_date, time(5, 0))
                wakeup_dt = max(dynamic_wakeup, earliest_allowed)
                
                ready_dt = wakeup_dt + timedelta(minutes=90)
                start_clk_dt = ready_dt
                
                day_end_limit = datetime.combine(current_date, time(23, 0)) 
                end_node_coords = self.hotel_coords
                
            else:
                wakeup_dt = datetime.combine(current_date, time()) + self.wakeup_delta
                ready_dt = wakeup_dt + timedelta(minutes=90)
                start_clk_dt = ready_dt
                day_end_limit = datetime.combine(current_date, profile["end_time"])
                end_node_coords = self.hotel_coords

            start_min = start_clk_dt.hour * 60 + start_clk_dt.minute
            end_limit_min = day_end_limit.hour * 60 + day_end_limit.minute
            end_min = end_limit_min
            
            if is_excursion:
                daily_pool = [p for p in excursion_day_map[day_idx] if p['id'] not in assigned_ids]

            elif day_idx in home_days:
                hint = day_cluster_hint.get(day_idx, set())
                unassigned = [p for p in remaining_home_pois if p['id'] not in assigned_ids]
                daily_pool = (
                    [p for p in unassigned if p['id'] in hint] +
                    [p for p in unassigned if p['id'] not in hint]
                )

            else:
                daily_pool = []
                
            nodes = []
            nodes.append({"id": "start", "type": "logistics", "lat": self.hotel_coords[0], "lon": self.hotel_coords[1], "duration": 0, "penalty": 0})
            
            for p in daily_pool:
                raw_dur = p.get('recommended_duration_mins', 120)
                windows = self._get_time_window(p.get("opening_hours"), current_date, raw_dur)
                if not windows: continue 
                
                bucket = p.get('bucket', 'want').lower()
                penalty = self.priority_weights.get(bucket, 1000)
                nodes.append({
                    "id": p['id'], "type": "attraction", "lat": p['latitude'], "lon": p['longitude'], 
                    "duration": raw_dur, "bucket": bucket, "penalty": penalty, 
                    "open_min": windows[0], "max_start_min": windows[1], "poi_data": p
                })
            
            if start_min < 15*60 and end_min > 13*60:
                nodes.append({
                    "id": "lunch", "type": "meal", "name": "Lunch Break", "lat": self.hotel_coords[0], "lon": self.hotel_coords[1], 
                    "duration": self.lunch_duration_mins, "penalty": 500000, 
                    "open_min": 12 * 60 + 30, "max_start_min": 16 * 60
                })
                
            nodes.append({"id": "end", "type": "logistics", "lat": end_node_coords[0], "lon": end_node_coords[1], "duration": 0, "penalty": 0})

            route = self._solve_day_route(nodes, start_min, end_min, transit_lookup)

            if route and len(route) >= 2:
                if day_idx != 0:
                    leave_hotel_dt = base_dt + timedelta(minutes=route[0]['dep_min'])
                    day_plan.append({
                        "type": "attraction", "id": f"start_hotel_{day_idx}", "name": "Start Day at Hotel", "bucket": "logistics",
                        "start_time": wakeup_dt.strftime("%H:%M"), "end_time": leave_hotel_dt.strftime("%H:%M"),
                        "transit_mins": 0, "unknown_hours_warning": False, "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1]
                    })
                
                last_real_lat, last_real_lon = self.hotel_coords[0], self.hotel_coords[1]
                
                for i in range(1, len(route) - 1):
                    prev_r, curr_r = route[i-1], route[i]
                    c_node = curr_r['node']
                    
                    node_start = base_dt + timedelta(minutes=curr_r['arr_min'])
                    node_end = base_dt + timedelta(minutes=curr_r['dep_min'])
                    
                    if c_node['type'] == 'meal':
                        t_mins = 5
                        t_leg = {"is_verified": False, "mode": "walking", "steps": [], "distance_text": "Nearby"}
                    else:
                        est_mins = self._get_base_transit_mins(last_real_lat, last_real_lon, c_node['lat'], c_node['lon'])
                        t_mins, t_leg = self._resolve_transit_leg(last_real_lat, last_real_lon, c_node['lat'], c_node['lon'], transit_lookup, est_mins)
                        last_real_lat, last_real_lon = c_node['lat'], c_node['lon']
                    
                    time_gap = curr_r['arr_min'] - (prev_r['dep_min'] + t_mins)
                    
                    if 0 < time_gap < 15:
                        t_mins += time_gap
                        time_gap = 0
                        
                    if time_gap >= 15:
                        wait_start = base_dt + timedelta(minutes=(prev_r['dep_min'] + t_mins))
                        day_plan.append({
                            "type": "free_time", "name": "Free Time / Wait",
                            "start_time": wait_start.strftime("%H:%M"), "end_time": node_start.strftime("%H:%M")
                        })
                        
                    if c_node['type'] == 'meal':
                        day_plan.append({
                            "type": "meal", "name": c_node['name'], "start_time": node_start.strftime("%H:%M"), "end_time": node_end.strftime("%H:%M")
                        })
                    else:
                        p_data = c_node['poi_data']
                        assigned_ids.add(p_data['id'])
                        day_plan.append({
                            "type": "attraction", "id": p_data['id'], "name": p_data['name'], "bucket": c_node['bucket'],
                            "start_time": node_start.strftime("%H:%M"), "end_time": node_end.strftime("%H:%M"),
                            "transit_mins": t_mins, "unknown_hours_warning": False,
                            "latitude": p_data['latitude'], "longitude": p_data['longitude'], "image_url": p_data.get('image_url'),
                            "transit_leg": t_leg
                        })

                end_r = route[-1]
                final_arr = base_dt + timedelta(minutes=end_r['arr_min'])
                
                if day_idx == total_days - 1:
                    est_mins = self._get_base_transit_mins(last_real_lat, last_real_lon, self.airport_coords[0], self.airport_coords[1])
                    t_mins, t_leg = self._resolve_transit_leg(last_real_lat, last_real_lon, self.airport_coords[0], self.airport_coords[1], transit_lookup, est_mins)
                    
                    day_plan.append({
                        "type": "attraction", "id": "dep_airport", "name": "Airport Check-in & Security", "bucket": "logistics",
                        "start_time": final_arr.strftime("%H:%M"), "end_time": self.departure_dt.strftime("%H:%M"),
                        "transit_mins": t_mins, "latitude": self.airport_coords[0], "longitude": self.airport_coords[1],
                        "unknown_hours_warning": False, "transit_leg": t_leg
                    })
                else:
                    est_mins = self._get_base_transit_mins(last_real_lat, last_real_lon, self.hotel_coords[0], self.hotel_coords[1])
                    t_mins, t_leg = self._resolve_transit_leg(last_real_lat, last_real_lon, self.hotel_coords[0], self.hotel_coords[1], transit_lookup, est_mins)
                    
                    day_plan.append({
                        "type": "attraction", "id": f"return_hotel_{day_idx}", "name": "Return to Hotel", "bucket": "logistics",
                        "start_time": final_arr.strftime("%H:%M"), "end_time": final_arr.strftime("%H:%M"),
                        "transit_mins": t_mins, "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1],
                        "unknown_hours_warning": False, "transit_leg": t_leg
                    })
            elif day_idx != 0:
                day_plan.append({
                    "type": "attraction", "id": f"start_hotel_{day_idx}", "name": "Start Day at Hotel", "bucket": "logistics",
                    "start_time": wakeup_dt.strftime("%H:%M"), "end_time": start_clk_dt.strftime("%H:%M"),
                    "transit_mins": 0, "unknown_hours_warning": False, "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1]
                })

            if day_plan:
                schedule.append({"day_index": day_idx, "date": current_date.strftime("%Y-%m-%d"), "events": day_plan})

        excluded = {"must": [], "want": [], "optional": []}
        for p in pois:
            if p['id'] not in assigned_ids:
                bucket = p.get('bucket', 'optional').lower()
                if bucket not in excluded: bucket = "optional"
                excluded[bucket].append({"id": p["id"], "name": p["name"], "bucket": bucket, "type": "attraction"})

        return {"status": "success", "schedule": schedule, "excluded": excluded}

    def _is_open_interval(self, arrival_dt: datetime, departure_dt: datetime, opening_hours_str: Any) -> tuple[bool, bool]:
        """
        Returns (is_open, is_unknown).
        Mirrors the same parsing logic as _get_time_window so that both methods
        handle bytes, "24/7", "24 hours", "null", "closed", etc. identically.
        Used only for generating the unknown_hours_warning flag on each event —
        it never affects scheduling decisions.
        """
        if not opening_hours_str: return True, True
        day_of_week = arrival_dt.strftime('%A').lower()
        try:
            if isinstance(opening_hours_str, bytes):
                opening_hours_str = opening_hours_str.decode('utf-8')
            if isinstance(opening_hours_str, str):
                hours_dict = json.loads(opening_hours_str)
            elif isinstance(opening_hours_str, dict):
                hours_dict = opening_hours_str
            else:
                return True, True

            day_hours = hours_dict.get(day_of_week)
            if day_hours is None or str(day_hours).lower() == "null": return True, True
            if "closed" in str(day_hours).lower(): return False, False

            day_str = str(day_hours).lower().strip()
            if "24/7" in day_str or "24 hours" in day_str or "00:00-24:00" in day_str or day_str == "24":
                return True, False

            if "-" in day_str:
                open_str, close_str = day_str.split("-", 1)
                open_t = datetime.strptime(open_str.strip(), "%H:%M").time()
                close_t = datetime.strptime(close_str.strip(), "%H:%M").time()
                arr_t = arrival_dt.time()
                dep_t = departure_dt.time()
                if open_t <= close_t:
                    return (open_t <= arr_t and dep_t <= close_t), False
                else:
                    return (arr_t >= open_t or dep_t <= close_t), False

        except Exception as e:
            log.warning(f"_is_open_interval: failed to parse opening hours: {e}")
            return True, True
        return True, False

    def recalculate_user_timeline(
        self, user_days_poi_ids: List[List[int]], pois: List[Dict[str, Any]], 
        existing_transit_legs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        poi_map = {p['id']: p for p in pois}
        schedule = []
        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        transit_lookup = existing_transit_legs or {}

        _LOGISTICS_PREFIXES = ("start_", "return_", "arr_", "dep_", "transit_")

        def _is_logistics_id(pid) -> bool:
            return isinstance(pid, str) and any(pid.startswith(pfx) for pfx in _LOGISTICS_PREFIXES)

        def _real_pois_for_day(id_list: list) -> List[Dict]:
            """Return resolved POI dicts for a day, skipping logistics anchors."""
            result = []
            for pid in id_list:
                if _is_logistics_id(pid):
                    continue
                p = poi_map.get(pid)
                if p:
                    result.append(p)
            return result

        for day_idx, day_poi_ids in enumerate(user_days_poi_ids):
            current_date = self.arrival_dt.date() + timedelta(days=day_idx)
            day_plan = []
            current_loc = self.hotel_coords
            lunch_taken = False

            real_pois_today = _real_pois_for_day(day_poi_ids)
            first_real_poi = real_pois_today[0] if real_pois_today else None

            ideal_wakeup_dt = datetime.combine(current_date, time()) + self.wakeup_delta

            is_excursion_day = any(
                self._get_real_distance_km(
                    self.hotel_coords[0], self.hotel_coords[1],
                    p['latitude'], p['longitude']
                ) > 55
                for p in real_pois_today
            )

            if is_excursion_day and real_pois_today:
                max_transit_mins = max(
                    self._get_base_transit_mins(
                        self.hotel_coords[0], self.hotel_coords[1],
                        p['latitude'], p['longitude']
                    )
                    for p in real_pois_today
                )
                shift_mins = min(max_transit_mins, 120)
                earliest_allowed = datetime.combine(current_date, time(5, 0))
                wakeup_dt = max(ideal_wakeup_dt - timedelta(minutes=shift_mins), earliest_allowed)

            elif day_idx == total_days - 1:
                est_dep_mins = self._get_base_transit_mins(
                    self.hotel_coords[0], self.hotel_coords[1],
                    self.airport_coords[0], self.airport_coords[1]
                )
                dep_transit_mins, _ = self._resolve_transit_leg(
                    self.hotel_coords[0], self.hotel_coords[1],
                    self.airport_coords[0], self.airport_coords[1],
                    transit_lookup, est_dep_mins
                )
                day_end_limit = self.departure_dt - timedelta(minutes=self.pre_flight_buffer_mins)
                latest_leave_time = day_end_limit - timedelta(minutes=dep_transit_mins)

                tentative_ready = ideal_wakeup_dt + timedelta(minutes=90)
                if tentative_ready > latest_leave_time:
                    wakeup_dt = latest_leave_time - timedelta(minutes=90)
                else:
                    wakeup_dt = ideal_wakeup_dt

            else:
                wakeup_dt = ideal_wakeup_dt

            ready_dt = wakeup_dt + timedelta(minutes=90)

            if day_idx == 0:
                bags_claim_end = self.arrival_dt + timedelta(minutes=self.airport_egress_mins)
                day_plan.append({
                    "type": "attraction", "id": "arr_airport", "name": "Customs & Baggage Claim", "bucket": "logistics",
                    "start_time": self.arrival_dt.strftime("%H:%M"), "end_time": bags_claim_end.strftime("%H:%M"),
                    "transit_mins": 0, "unknown_hours_warning": False,
                    "latitude": self.airport_coords[0], "longitude": self.airport_coords[1]
                })
                est_arr_mins = self._get_base_transit_mins(
                    self.airport_coords[0], self.airport_coords[1],
                    self.hotel_coords[0], self.hotel_coords[1]
                )
                h_transit, h_leg = self._resolve_transit_leg(
                    self.airport_coords[0], self.airport_coords[1],
                    self.hotel_coords[0], self.hotel_coords[1],
                    transit_lookup, est_arr_mins
                )
                hotel_arrival_time = bags_claim_end + timedelta(minutes=h_transit)
                checkin_end_time = hotel_arrival_time + timedelta(minutes=self.hotel_checkin_mins)
                day_plan.append({
                    "type": "attraction", "id": "arr_hotel", "name": "Check-in & Settle at Hotel", "bucket": "logistics",
                    "start_time": hotel_arrival_time.strftime("%H:%M"), "end_time": checkin_end_time.strftime("%H:%M"),
                    "transit_mins": h_transit, "unknown_hours_warning": False,
                    "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1], "transit_leg": h_leg
                })
                current_clock = max(checkin_end_time, ready_dt)

            else:
                current_clock = ready_dt

            if day_idx != 0:
                if first_real_poi is not None:
                    day_plan.append({
                        "type": "attraction", "id": f"start_hotel_{day_idx}", "name": "Start Day at Hotel", "bucket": "logistics",
                        "start_time": wakeup_dt.strftime("%H:%M"), "end_time": ready_dt.strftime("%H:%M"),
                        "transit_mins": 0, "unknown_hours_warning": False,
                        "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1]
                    })
                else:
                    day_plan.append({
                        "type": "attraction", "id": f"start_hotel_{day_idx}", "name": "Start Day at Hotel", "bucket": "logistics",
                        "start_time": wakeup_dt.strftime("%H:%M"), "end_time": ready_dt.strftime("%H:%M"),
                        "transit_mins": 0, "unknown_hours_warning": False,
                        "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1]
                    })
                    current_clock = ready_dt

            for poi_id in day_poi_ids:
                if _is_logistics_id(poi_id):
                    continue

                p = poi_map.get(poi_id)
                if not p:
                    continue

                if current_clock.hour >= 13 and not lunch_taken:
                    day_plan.append({
                        "type": "meal", "name": "Lunch Break",
                        "start_time": current_clock.strftime("%H:%M"),
                        "end_time": (current_clock + timedelta(minutes=self.lunch_duration_mins)).strftime("%H:%M")
                    })
                    current_clock += timedelta(minutes=self.lunch_duration_mins)
                    lunch_taken = True

                est_mins = self._get_base_transit_mins(
                    current_loc[0], current_loc[1], p['latitude'], p['longitude']
                )
                final_transit_mins, transit_leg_state = self._resolve_transit_leg(
                    current_loc[0], current_loc[1], p['latitude'], p['longitude'],
                    transit_lookup, est_mins
                )

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
                    "transit_leg": transit_leg_state
                })

                current_clock = dep_dt
                current_loc = (p['latitude'], p['longitude'])

            if day_idx != total_days - 1 and first_real_poi is not None:
                est_ret_mins = self._get_base_transit_mins(
                    current_loc[0], current_loc[1],
                    self.hotel_coords[0], self.hotel_coords[1]
                )
                ret_transit_mins, ret_leg = self._resolve_transit_leg(
                    current_loc[0], current_loc[1],
                    self.hotel_coords[0], self.hotel_coords[1],
                    transit_lookup, est_ret_mins
                )
                return_dt = current_clock + timedelta(minutes=ret_transit_mins)
                day_plan.append({
                    "type": "attraction", "id": f"return_hotel_{day_idx}", "name": "Return to Hotel", "bucket": "logistics",
                    "start_time": return_dt.strftime("%H:%M"), "end_time": return_dt.strftime("%H:%M"),
                    "transit_mins": ret_transit_mins,
                    "latitude": self.hotel_coords[0], "longitude": self.hotel_coords[1],
                    "unknown_hours_warning": False, "transit_leg": ret_leg
                })
                current_clock = return_dt

            if day_idx == total_days - 1:
                airport_arrival_target = self.departure_dt - timedelta(minutes=self.pre_flight_buffer_mins)
                est_dep_mins = self._get_base_transit_mins(
                    current_loc[0], current_loc[1],
                    self.airport_coords[0], self.airport_coords[1]
                )
                airport_transit_mins, dep_leg = self._resolve_transit_leg(
                    current_loc[0], current_loc[1],
                    self.airport_coords[0], self.airport_coords[1],
                    transit_lookup, est_dep_mins
                )
                leave_for_airport_dt = airport_arrival_target - timedelta(minutes=airport_transit_mins)

                if current_clock < leave_for_airport_dt:
                    day_plan.append({
                        "type": "free_time", "id": "free_time_hotel", "name": "Relax / Prep for Departure",
                        "start_time": current_clock.strftime("%H:%M"),
                        "end_time": leave_for_airport_dt.strftime("%H:%M")
                    })

                day_plan.append({
                    "type": "attraction", "id": "dep_airport", "name": "Airport Check-in & Security", "bucket": "logistics",
                    "start_time": airport_arrival_target.strftime("%H:%M"), "end_time": self.departure_dt.strftime("%H:%M"),
                    "transit_mins": airport_transit_mins,
                    "latitude": self.airport_coords[0], "longitude": self.airport_coords[1],
                    "unknown_hours_warning": False, "transit_leg": dep_leg
                })

            schedule.append({"day_index": day_idx, "date": current_date.strftime("%Y-%m-%d"), "events": day_plan})

        assigned_ids = set()
        for day in schedule:
            for event in day["events"]:
                if event.get("type") == "attraction" and "id" in event:
                    pid = event["id"]
                    if isinstance(pid, int) or (isinstance(pid, str) and pid.isdigit()):
                        assigned_ids.add(int(pid) if isinstance(pid, str) else pid)

        excluded = {"must": [], "want": [], "optional": []}
        
        for p in pois:
            if p['id'] not in assigned_ids:
                bucket = p.get('bucket', 'optional').lower()
                if bucket not in excluded: bucket = "optional"
                excluded[bucket].append({"id": p["id"], "name": p["name"], "bucket": bucket, "type": "attraction"})

        return {"status": "success", "schedule": schedule, "excluded": excluded}
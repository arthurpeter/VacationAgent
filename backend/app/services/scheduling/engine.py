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

CITY_DISTANCE_THRESHOLD_KM = 50


class ScheduleEngine:
    def __init__(
        self,
        pace: str,
        arrival_dt: datetime,
        departure_dt: datetime,
        hotel_coords: tuple,
        airport_coords: tuple,
        wakeup_time: str = "08:00",
        lunch_duration_mins: int = 90,
    ):

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
            "fast-paced": {"end_time": time(22, 30)},
        }

    def _get_real_distance_km(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _get_base_transit_mins(self, lat1, lon1, lat2, lon2):
        straight_dist = self._get_real_distance_km(lat1, lon1, lat2, lon2)
        if straight_dist < 0.1:
            return 2

        if straight_dist < 1.0:
            dist_km = straight_dist * 1.35
            return 2 + int((dist_km / 4.0) * 60)

        straight_dist -= 1.0

        if straight_dist < 19.0:
            dist_km = straight_dist * 1.35
            return 5 + int((1.35 / 4.0) * 60) + int((dist_km / 25.0) * 60)

        straight_dist -= 19.0
        return (
            15
            + int((1.35 / 4.0) * 60)
            + int((25.65 / 25.0) * 60)
            + int((straight_dist / 130.0) * 60)
        )

    def _resolve_transit_leg(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        transit_lookup: dict,
        default_mins: int,
    ) -> tuple[int, dict]:
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
                "distance_text": mode_bundle.get("distance_text", ""),
                "alternatives": leg_meta.get("alternatives"),
            }
        return default_mins, {
            "is_verified": False,
            "mode": "estimated",
            "polyline": None,
            "steps": [],
            "distance_text": "",
        }

    def _get_time_window(
        self, opening_hours_str: Any, date_obj: datetime, duration_mins: int
    ) -> Optional[tuple[int, int]]:
        fallback = (0, 1440 - duration_mins)
        if not opening_hours_str:
            return fallback

        day_of_week = date_obj.strftime("%A").lower()
        try:
            if isinstance(opening_hours_str, bytes):
                opening_hours_str = opening_hours_str.decode("utf-8")

            if isinstance(opening_hours_str, str):
                hours_dict = json.loads(opening_hours_str)
            elif isinstance(opening_hours_str, dict):
                hours_dict = opening_hours_str
            else:
                return fallback

            day_hours = hours_dict.get(day_of_week)
            if day_hours is None or str(day_hours).lower() == "null":
                return fallback
            if "closed" in str(day_hours).lower():
                return None
            if "24" in str(day_hours).lower() or "00:00-24:00" in str(day_hours):
                return fallback

            if "-" in str(day_hours):
                open_str, close_str = str(day_hours).split("-")
                open_t = datetime.strptime(open_str.strip(), "%H:%M").time()
                close_t = datetime.strptime(close_str.strip(), "%H:%M").time()

                open_min = open_t.hour * 60 + open_t.minute
                close_min = close_t.hour * 60 + close_t.minute

                if close_min < open_min:
                    close_min += 1440

                    if close_min > 1440:
                        close_min = 1440

                max_start = close_min - duration_mins
                if max_start < open_min:
                    return None
                return (open_min, max_start)

        except Exception as e:
            log.warning(
                f"Failed to parse opening hours: {e} | Defaulting to Always Open."
            )

        return fallback

    def _cluster_pois(self, pois: List[Dict], k: int) -> Dict[int, List[Dict]]:
        if not pois or k <= 1:
            return {0: pois}
        if k >= len(pois):
            return {i: [p] for i, p in enumerate(pois)}

        coords = np.array([[p["latitude"], p["longitude"]] for p in pois])
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto").fit(coords)

        clusters = {i: [] for i in range(k)}
        for i, label in enumerate(kmeans.labels_):
            clusters[label].append(pois[i])

        return clusters

    def _balance_clusters(
        self,
        clusters: Dict[int, List[Dict]],
        max_distance_km: float = 8.0,
        max_passes: int = 20,
        tolerance_mins: int = 30,
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
            return sum(p.get("recommended_duration_mins", 120) for p in pois)

        def _centroid(pois: List[Dict]) -> tuple[float, float]:
            if not pois:
                return (0.0, 0.0)
            lats = [p["latitude"] for p in pois]
            lons = [p["longitude"] for p in pois]
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
                p
                for p in balanced[max_k]
                if self._get_real_distance_km(
                    p["latitude"], p["longitude"], dest_centroid[0], dest_centroid[1]
                )
                <= max_distance_km
            ]

            if not candidates:
                break

            candidates.sort(
                key=lambda p: (
                    priority_order.get(p.get("bucket", "want").lower(), 1),
                    self._get_real_distance_km(
                        p["latitude"],
                        p["longitude"],
                        dest_centroid[0],
                        dest_centroid[1],
                    ),
                )
            )

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

    def _solve_day_route(
        self, day_nodes: List[Dict], start_min: int, end_min: int, transit_lookup: dict
    ):
        num_nodes = len(day_nodes)
        if num_nodes < 2:
            return []
        manager = pywrapcp.RoutingIndexManager(num_nodes, 1, [0], [num_nodes - 1])
        routing = pywrapcp.RoutingModel(manager)

        time_matrix = [[0] * num_nodes for _ in range(num_nodes)]

        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    time_matrix[i][j] = 0
                    continue

                n1, n2 = day_nodes[i], day_nodes[j]

                if n1["type"] == "meal" or n2["type"] == "meal":
                    transit = 5
                else:
                    est_mins = self._get_base_transit_mins(
                        n1["lat"], n1["lon"], n2["lat"], n2["lon"]
                    )
                    transit, _ = self._resolve_transit_leg(
                        n1["lat"],
                        n1["lon"],
                        n2["lat"],
                        n2["lon"],
                        transit_lookup,
                        est_mins,
                    )

                time_matrix[i][j] = transit + n1["duration"]

        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return time_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        routing.AddDimension(transit_callback_index, 180, 2880, False, "Time")
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

            poi_open = int(node["open_min"])
            poi_close = int(max(poi_open, node["max_start_min"]))

            time_dimension.CumulVar(index).SetRange(poi_open, poi_close)
            routing.AddDisjunction([index], int(node["penalty"]))

            if node["type"] == "meal":
                ideal_lunch = int(safe_start + (5 * 60))
                time_dimension.SetCumulVarSoftLowerBound(index, ideal_lunch, 10)
                time_dimension.SetCumulVarSoftUpperBound(index, ideal_lunch, 10)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 1

        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            log.warning("Solver failed to find a feasible solution.")
            return []

        route = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node_idx = manager.IndexToNode(index)
            arr_min = solution.Value(time_dimension.CumulVar(index))
            route.append(
                {
                    "node": day_nodes[node_idx],
                    "arr_min": arr_min,
                    "dep_min": arr_min + day_nodes[node_idx]["duration"],
                }
            )
            index = solution.Value(routing.NextVar(index))

        node_idx = manager.IndexToNode(index)
        arr_min = solution.Value(time_dimension.CumulVar(index))
        route.append(
            {"node": day_nodes[node_idx], "arr_min": arr_min, "dep_min": arr_min}
        )

        return route

    def _build_day_context(
        self,
        day_idx: int,
        total_days: int,
        excursion_day_map: Dict[int, List[Dict]],
        profile: Dict,
    ) -> Dict:
        """
        Compute all time-boundary and coordinate context for a single day.
        Returns a dict with keys: current_date, wakeup_dt, ready_dt,
        start_clk_dt, start_min, end_min, end_node_coords, is_excursion.
        """
        current_date = self.arrival_dt.date() + timedelta(days=day_idx)
        is_excursion = day_idx in excursion_day_map

        if day_idx == 0:
            wakeup_dt = datetime.combine(current_date, time()) + self.wakeup_delta
            ready_dt = wakeup_dt + timedelta(minutes=90)
            bags_claim_end = self.arrival_dt + timedelta(
                minutes=self.airport_egress_mins
            )

            start_clk_dt = max(
                bags_claim_end + timedelta(minutes=self.hotel_checkin_mins),
                ready_dt,
            )
            base_cutoff = profile["end_time"]
            early_cutoff_mins = min(base_cutoff.hour * 60 + base_cutoff.minute, 20 * 60)
            day_end_limit = datetime.combine(
                current_date, time(early_cutoff_mins // 60, early_cutoff_mins % 60)
            )
            end_node_coords = self.hotel_coords

        elif day_idx == total_days - 1:
            wakeup_dt = datetime.combine(current_date, time()) + self.wakeup_delta
            ready_dt = wakeup_dt + timedelta(minutes=90)
            day_end_limit = self.departure_dt - timedelta(
                minutes=self.pre_flight_buffer_mins
            )
            est_dep_mins = self._get_base_transit_mins(
                self.hotel_coords[0],
                self.hotel_coords[1],
                self.airport_coords[0],
                self.airport_coords[1],
            )
            dep_transit_mins, _ = self._resolve_transit_leg(
                self.hotel_coords[0],
                self.hotel_coords[1],
                self.airport_coords[0],
                self.airport_coords[1],
                {},
                est_dep_mins,
            )
            latest_leave_time = day_end_limit - timedelta(minutes=dep_transit_mins)
            if ready_dt > latest_leave_time:
                ready_dt = latest_leave_time
                wakeup_dt = ready_dt - timedelta(minutes=90)
            start_clk_dt = ready_dt
            end_node_coords = self.airport_coords

        elif is_excursion:
            max_transit_mins = max(
                self._get_base_transit_mins(
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    p["latitude"],
                    p["longitude"],
                )
                for p in excursion_day_map[day_idx]
            )
            ideal_wakeup = datetime.combine(current_date, time()) + self.wakeup_delta
            shift_mins = min(max_transit_mins, 120)
            earliest_allowed = datetime.combine(current_date, time(5, 0))
            wakeup_dt = max(
                ideal_wakeup - timedelta(minutes=shift_mins), earliest_allowed
            )
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
        end_min = day_end_limit.hour * 60 + day_end_limit.minute

        return {
            "current_date": current_date,
            "wakeup_dt": wakeup_dt,
            "ready_dt": ready_dt,
            "start_clk_dt": start_clk_dt,
            "start_min": start_min,
            "end_min": end_min,
            "end_node_coords": end_node_coords,
            "is_excursion": is_excursion,
        }

    def _estimate_day_free_mins(
        self,
        ctx: Dict,
        assigned_pois: List[Dict],
        transit_lookup: dict,
        candidate_poi: Optional[Dict] = None,
        solved_route: Optional[List[Dict]] = None,
    ) -> int:
        """
        Estimate remaining schedulable minutes in a day.

        Uses the already-solved OR-Tools route as the source of truth so we
        never drift from what the solver actually committed to.  The arithmetic
        path (no route available) is kept only as a fallback for day 0 / last
        day where no attractions are ever scheduled.

        Args:
            ctx:            Day context dict from _build_day_context.
            assigned_pois:  POIs already committed to this day (used only in
                            the fallback path).
            transit_lookup: Verified transit legs dict.
            candidate_poi:  The POI we are trying to squeeze in (optional).
                            When provided, its duration *and* the transit from
                            the current last real location to it are subtracted
                            from the remaining slack so the caller gets a
                            conservative "will it fit?" answer.
            solved_route:   The OR-Tools route list for this day as returned by
                            _solve_day_route.  When present this is the primary
                            source; otherwise we fall back to arithmetic.

        Returns:
            Estimated free minutes remaining (clamped to 0).
        """
        end_min = ctx["end_min"]

        if solved_route and len(solved_route) >= 2:
            last_dep_min = ctx["start_min"]
            last_real_lat, last_real_lon = self.hotel_coords

            for step in solved_route[1:-1]:
                n = step["node"]
                if n["type"] in ("attraction",) and n["id"] not in ("lunch",):
                    last_dep_min = step["dep_min"]
                    last_real_lat = n["lat"]
                    last_real_lon = n["lon"]
                elif n["type"] == "meal":
                    last_dep_min = step["dep_min"]

            slack = end_min - last_dep_min

            est_return = self._get_base_transit_mins(
                last_real_lat,
                last_real_lon,
                ctx["end_node_coords"][0],
                ctx["end_node_coords"][1],
            )
            ret_mins, _ = self._resolve_transit_leg(
                last_real_lat,
                last_real_lon,
                ctx["end_node_coords"][0],
                ctx["end_node_coords"][1],
                transit_lookup,
                est_return,
            )
            slack -= ret_mins

            if candidate_poi is not None:
                poi_dur = candidate_poi.get("recommended_duration_mins", 120)
                est_to_poi = self._get_base_transit_mins(
                    last_real_lat,
                    last_real_lon,
                    candidate_poi["latitude"],
                    candidate_poi["longitude"],
                )
                transit_to_poi, _ = self._resolve_transit_leg(
                    last_real_lat,
                    last_real_lon,
                    candidate_poi["latitude"],
                    candidate_poi["longitude"],
                    transit_lookup,
                    est_to_poi,
                )
                slack -= poi_dur + transit_to_poi

            return max(0, slack)

        used = sum(p.get("recommended_duration_mins", 120) for p in assigned_pois)

        prev_lat, prev_lon = self.hotel_coords
        transit_used = 0
        for p in assigned_pois:
            est = self._get_base_transit_mins(
                prev_lat, prev_lon, p["latitude"], p["longitude"]
            )
            t, _ = self._resolve_transit_leg(
                prev_lat, prev_lon, p["latitude"], p["longitude"], transit_lookup, est
            )
            transit_used += t
            prev_lat, prev_lon = p["latitude"], p["longitude"]

        est = self._get_base_transit_mins(
            prev_lat,
            prev_lon,
            ctx["end_node_coords"][0],
            ctx["end_node_coords"][1],
        )
        t, _ = self._resolve_transit_leg(
            prev_lat,
            prev_lon,
            ctx["end_node_coords"][0],
            ctx["end_node_coords"][1],
            transit_lookup,
            est,
        )
        transit_used += t

        if candidate_poi is not None:
            poi_dur = candidate_poi.get("recommended_duration_mins", 120)
            est_to_poi = self._get_base_transit_mins(
                prev_lat,
                prev_lon,
                candidate_poi["latitude"],
                candidate_poi["longitude"],
            )
            transit_to_poi, _ = self._resolve_transit_leg(
                prev_lat,
                prev_lon,
                candidate_poi["latitude"],
                candidate_poi["longitude"],
                transit_lookup,
                est_to_poi,
            )
            used += poi_dur + transit_to_poi

        total_window = end_min - ctx["start_min"]
        return max(0, total_window - used - transit_used - self.lunch_duration_mins)

    def _build_route_events(
        self,
        day_idx: int,
        total_days: int,
        ctx: Dict,
        route: List[Dict],
        transit_lookup: dict,
    ) -> List[Dict]:
        """
        Convert a solved OR-Tools route into the flat list of event dicts
        that populate day_plan.  Handles logistics bookends, free-time gaps,
        and meal blocks identically to the original implementation.
        """
        base_dt = datetime.combine(ctx["current_date"], time.min)
        wakeup_dt = ctx["wakeup_dt"]
        day_plan: List[Dict] = []

        if not route or len(route) < 2:
            return day_plan

        if day_idx != 0:
            leave_hotel_dt = base_dt + timedelta(minutes=route[0]["dep_min"])
            day_plan.append(
                {
                    "type": "attraction",
                    "id": f"start_hotel_{day_idx}",
                    "name": "Start Day at Hotel",
                    "bucket": "logistics",
                    "start_time": wakeup_dt.strftime("%H:%M"),
                    "end_time": leave_hotel_dt.strftime("%H:%M"),
                    "transit_mins": 0,
                    "unknown_hours_warning": False,
                    "latitude": self.hotel_coords[0],
                    "longitude": self.hotel_coords[1],
                }
            )

        last_real_lat, last_real_lon = self.hotel_coords

        for i in range(1, len(route) - 1):
            prev_r, curr_r = route[i - 1], route[i]
            c_node = curr_r["node"]

            node_start = base_dt + timedelta(minutes=curr_r["arr_min"])
            node_end = base_dt + timedelta(minutes=curr_r["dep_min"])

            if c_node["type"] == "meal":
                t_mins = 5
                t_leg = {
                    "is_verified": False,
                    "mode": "walking",
                    "steps": [],
                    "distance_text": "Nearby",
                }
            else:
                est_mins = self._get_base_transit_mins(
                    last_real_lat, last_real_lon, c_node["lat"], c_node["lon"]
                )
                t_mins, t_leg = self._resolve_transit_leg(
                    last_real_lat,
                    last_real_lon,
                    c_node["lat"],
                    c_node["lon"],
                    transit_lookup,
                    est_mins,
                )
                last_real_lat, last_real_lon = c_node["lat"], c_node["lon"]

            time_gap = curr_r["arr_min"] - (prev_r["dep_min"] + t_mins)

            if 0 < time_gap < 15:
                t_mins += time_gap
                time_gap = 0

            if time_gap >= 15:
                wait_start = base_dt + timedelta(minutes=(prev_r["dep_min"] + t_mins))
                day_plan.append(
                    {
                        "type": "free_time",
                        "name": "Free Time / Wait",
                        "start_time": wait_start.strftime("%H:%M"),
                        "end_time": node_start.strftime("%H:%M"),
                    }
                )

            if c_node["type"] == "meal":
                day_plan.append(
                    {
                        "type": "meal",
                        "name": c_node["name"],
                        "start_time": node_start.strftime("%H:%M"),
                        "end_time": node_end.strftime("%H:%M"),
                    }
                )
            else:
                p_data = c_node["poi_data"]
                day_plan.append(
                    {
                        "type": "attraction",
                        "id": p_data["id"],
                        "name": p_data["name"],
                        "bucket": c_node["bucket"],
                        "start_time": node_start.strftime("%H:%M"),
                        "end_time": node_end.strftime("%H:%M"),
                        "transit_mins": t_mins,
                        "unknown_hours_warning": False,
                        "latitude": p_data["latitude"],
                        "longitude": p_data["longitude"],
                        "image_url": p_data.get("image_url"),
                        "transit_leg": t_leg,
                    }
                )

        end_r = route[-1]
        final_arr = base_dt + timedelta(minutes=end_r["arr_min"])

        if day_idx == total_days - 1:
            est_mins = self._get_base_transit_mins(
                last_real_lat,
                last_real_lon,
                self.airport_coords[0],
                self.airport_coords[1],
            )
            t_mins, t_leg = self._resolve_transit_leg(
                last_real_lat,
                last_real_lon,
                self.airport_coords[0],
                self.airport_coords[1],
                transit_lookup,
                est_mins,
            )
            day_plan.append(
                {
                    "type": "attraction",
                    "id": "dep_airport",
                    "name": "Airport Check-in & Security",
                    "bucket": "logistics",
                    "start_time": final_arr.strftime("%H:%M"),
                    "end_time": self.departure_dt.strftime("%H:%M"),
                    "transit_mins": t_mins,
                    "latitude": self.airport_coords[0],
                    "longitude": self.airport_coords[1],
                    "unknown_hours_warning": False,
                    "transit_leg": t_leg,
                }
            )
        else:
            est_mins = self._get_base_transit_mins(
                last_real_lat,
                last_real_lon,
                self.hotel_coords[0],
                self.hotel_coords[1],
            )
            t_mins, t_leg = self._resolve_transit_leg(
                last_real_lat,
                last_real_lon,
                self.hotel_coords[0],
                self.hotel_coords[1],
                transit_lookup,
                est_mins,
            )
            day_plan.append(
                {
                    "type": "attraction",
                    "id": f"return_hotel_{day_idx}",
                    "name": "Return to Hotel",
                    "bucket": "logistics",
                    "start_time": final_arr.strftime("%H:%M"),
                    "end_time": final_arr.strftime("%H:%M"),
                    "transit_mins": t_mins,
                    "latitude": self.hotel_coords[0],
                    "longitude": self.hotel_coords[1],
                    "unknown_hours_warning": False,
                    "transit_leg": t_leg,
                }
            )

        return day_plan

    def _build_node_list(
        self,
        daily_pool: List[Dict],
        ctx: Dict,
        end_node_coords: tuple,
    ) -> List[Dict]:
        """
        Build the OR-Tools node list for a day from a pool of POIs.
        Adds start/end logistics nodes and a lunch node when appropriate.
        """
        nodes: List[Dict] = []
        nodes.append(
            {
                "id": "start",
                "type": "logistics",
                "lat": self.hotel_coords[0],
                "lon": self.hotel_coords[1],
                "duration": 0,
                "penalty": 0,
            }
        )

        current_date = ctx["current_date"]
        start_min = ctx["start_min"]
        end_min = ctx["end_min"]

        for p in daily_pool:
            raw_dur = p.get("recommended_duration_mins", 120)
            windows = self._get_time_window(
                p.get("opening_hours"), current_date, raw_dur
            )
            if not windows:
                continue
            bucket = p.get("bucket", "want").lower()
            penalty = self.priority_weights.get(bucket, 1000)
            nodes.append(
                {
                    "id": p["id"],
                    "type": "attraction",
                    "lat": p["latitude"],
                    "lon": p["longitude"],
                    "duration": raw_dur,
                    "bucket": bucket,
                    "penalty": penalty,
                    "open_min": windows[0],
                    "max_start_min": windows[1],
                    "poi_data": p,
                }
            )

        if start_min < 15 * 60 and end_min > 13 * 60:
            nodes.append(
                {
                    "id": "lunch",
                    "type": "meal",
                    "name": "Lunch Break",
                    "lat": self.hotel_coords[0],
                    "lon": self.hotel_coords[1],
                    "duration": self.lunch_duration_mins,
                    "penalty": 500000,
                    "open_min": 12 * 60 + 30,
                    "max_start_min": 16 * 60,
                }
            )

        nodes.append(
            {
                "id": "end",
                "type": "logistics",
                "lat": end_node_coords[0],
                "lon": end_node_coords[1],
                "duration": 0,
                "penalty": 0,
            }
        )

        return nodes

    def generate_schedule(
        self,
        pois: List[Dict[str, Any]],
        existing_transit_legs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build a day-by-day itinerary using a two-pass strategy that eliminates
        the priority-vacuum effect where early days absorb all high-value POIs.

        Pass 1 — Cluster-constrained solving
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Each home day is given exactly the POIs that K-Means + balance assigned
        to it.  OR-Tools may still drop some (time / opening-hours infeasible)
        but it cannot reach into another day's cluster to steal attractions.
        Excursion days are also solved in this pass with their dedicated POI set.

        Pass 2 — Leftover absorption
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Any POI not assigned in Pass 1 is ranked by (priority desc, proximity
        to receiving day's cluster centroid asc) and injected one-by-one into
        the day with the most remaining free time, re-solving that day's route
        after each successful insertion.  This guarantees every schedulable
        attraction finds a home without creating an ordering bias toward early
        days.
        """
        if not pois:
            return {"status": "success", "schedule": [], "excluded": {}}

        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        transit_lookup = existing_transit_legs or {}
        profile = self.pace_profiles.get(self.pace, self.pace_profiles["moderate"])

        home_pois: List[Dict] = []
        excursion_pois: List[Dict] = []
        for p in pois:
            if (
                self._get_real_distance_km(
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    p["latitude"],
                    p["longitude"],
                )
                > CITY_DISTANCE_THRESHOLD_KM
            ):
                excursion_pois.append(p)
            else:
                home_pois.append(p)

        active_days = list(range(total_days))
        full_days = [i for i in active_days if i != 0 and i != total_days - 1]

        excursion_groups: List[List[Dict]] = []
        for p in excursion_pois:
            placed = False
            for group in excursion_groups:
                if (
                    self._get_real_distance_km(
                        p["latitude"],
                        p["longitude"],
                        group[0]["latitude"],
                        group[0]["longitude"],
                    )
                    < 30
                ):
                    group.append(p)
                    placed = True
                    break
            if not placed:
                excursion_groups.append([p])

        excursion_day_map: Dict[int, List[Dict]] = {}
        for i, group in enumerate(excursion_groups):
            if i < len(full_days):
                target_day = full_days[i * (len(full_days) // len(excursion_groups))]
                excursion_day_map[target_day] = group
            else:
                log.warning(
                    f"More day trips ({len(excursion_groups)}) than available "
                    f"full days ({len(full_days)})!"
                )

        home_days = [d for d in full_days if d not in excursion_day_map]
        k_clusters = min(len(home_pois), len(home_days)) if home_days else 1
        raw_clusters = self._cluster_pois(home_pois, k_clusters)
        balanced_clusters = self._balance_clusters(raw_clusters)

        day_to_cluster: Dict[int, int] = {
            day_idx: i for i, day_idx in enumerate(home_days)
        }

        def _centroid(poi_list: List[Dict]) -> tuple[float, float]:
            if not poi_list:
                return self.hotel_coords
            return (
                sum(p["latitude"] for p in poi_list) / len(poi_list),
                sum(p["longitude"] for p in poi_list) / len(poi_list),
            )

        cluster_centroids: Dict[int, tuple] = {
            i: _centroid(pois_in_cluster)
            for i, pois_in_cluster in balanced_clusters.items()
        }

        assigned_ids: set = set()

        day_assigned_pois: Dict[int, List[Dict]] = {d: [] for d in active_days}

        day_routes: Dict[int, List[Dict]] = {}

        day_contexts: Dict[int, Dict] = {}

        day_node_lists: Dict[int, List[Dict]] = {}

        schedule_buffer: Dict[int, Dict] = {}

        for day_idx in active_days:
            ctx = self._build_day_context(
                day_idx, total_days, excursion_day_map, profile
            )
            day_contexts[day_idx] = ctx
            current_date = ctx["current_date"]
            base_dt = datetime.combine(current_date, time.min)
            wakeup_dt = ctx["wakeup_dt"]
            day_plan: List[Dict] = []

            if day_idx == 0:
                bags_claim_end = self.arrival_dt + timedelta(
                    minutes=self.airport_egress_mins
                )
                day_plan.append(
                    {
                        "type": "attraction",
                        "id": "arr_airport",
                        "name": "Customs & Baggage Claim",
                        "bucket": "logistics",
                        "start_time": self.arrival_dt.strftime("%H:%M"),
                        "end_time": bags_claim_end.strftime("%H:%M"),
                        "transit_mins": 0,
                        "unknown_hours_warning": False,
                        "latitude": self.airport_coords[0],
                        "longitude": self.airport_coords[1],
                    }
                )
                est_arr_mins = self._get_base_transit_mins(
                    self.airport_coords[0],
                    self.airport_coords[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                )
                h_transit, h_leg = self._resolve_transit_leg(
                    self.airport_coords[0],
                    self.airport_coords[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    transit_lookup,
                    est_arr_mins,
                )
                hotel_arrival_time = bags_claim_end + timedelta(minutes=h_transit)
                checkin_end_time = hotel_arrival_time + timedelta(
                    minutes=self.hotel_checkin_mins
                )
                day_plan.append(
                    {
                        "type": "attraction",
                        "id": "arr_hotel",
                        "name": "Check-in & Settle at Hotel",
                        "bucket": "logistics",
                        "start_time": hotel_arrival_time.strftime("%H:%M"),
                        "end_time": checkin_end_time.strftime("%H:%M"),
                        "transit_mins": h_transit,
                        "unknown_hours_warning": False,
                        "latitude": self.hotel_coords[0],
                        "longitude": self.hotel_coords[1],
                        "transit_leg": h_leg,
                    }
                )

            if ctx["is_excursion"]:
                daily_pool = [
                    p for p in excursion_day_map[day_idx] if p["id"] not in assigned_ids
                ]
            elif day_idx in home_days:
                cluster_idx = day_to_cluster[day_idx]
                daily_pool = [
                    p
                    for p in balanced_clusters.get(cluster_idx, [])
                    if p["id"] not in assigned_ids
                ]
            else:
                daily_pool = []

            nodes = self._build_node_list(daily_pool, ctx, ctx["end_node_coords"])
            day_node_lists[day_idx] = nodes
            route = self._solve_day_route(
                nodes, ctx["start_min"], ctx["end_min"], transit_lookup
            )
            day_routes[day_idx] = route

            solved_poi_ids: set = set()
            if route and len(route) >= 2:
                for step in route[1:-1]:
                    n = step["node"]
                    if n["type"] == "attraction" and n["id"] != "lunch":
                        solved_poi_ids.add(n["id"])
                        assigned_ids.add(n["id"])
                        day_assigned_pois[day_idx].append(n["poi_data"])

            route_events = self._build_route_events(
                day_idx, total_days, ctx, route, transit_lookup
            )
            day_plan.extend(route_events)

            if (not route or len(route) < 2) and day_idx != 0:
                day_plan.append(
                    {
                        "type": "attraction",
                        "id": f"start_hotel_{day_idx}",
                        "name": "Start Day at Hotel",
                        "bucket": "logistics",
                        "start_time": wakeup_dt.strftime("%H:%M"),
                        "end_time": ctx["start_clk_dt"].strftime("%H:%M"),
                        "transit_mins": 0,
                        "unknown_hours_warning": False,
                        "latitude": self.hotel_coords[0],
                        "longitude": self.hotel_coords[1],
                    }
                )

            schedule_buffer[day_idx] = {
                "day_index": day_idx,
                "date": current_date.strftime("%Y-%m-%d"),
                "events": day_plan,
                "_day_plan_prefix": day_plan,
            }

        priority_rank = {"must": 0, "want": 1, "optional": 2}
        leftovers: List[Dict] = [p for p in pois if p["id"] not in assigned_ids]

        leftovers.sort(
            key=lambda p: (
                priority_rank.get(p.get("bucket", "want").lower(), 1),
                p["id"],
            )
        )

        candidate_days = [d for d in active_days if d not in excursion_day_map]

        for leftover in leftovers:
            if leftover["id"] in assigned_ids:
                continue

            best_day = None
            best_score = None

            for day_idx in candidate_days:
                ctx = day_contexts[day_idx]

                free_mins = self._estimate_day_free_mins(
                    ctx,
                    day_assigned_pois[day_idx],
                    transit_lookup,
                    candidate_poi=leftover,
                    solved_route=day_routes.get(day_idx),
                )

                if free_mins <= 0:
                    continue

                cluster_idx = day_to_cluster.get(day_idx)
                if cluster_idx is not None and cluster_idx in cluster_centroids:
                    c_lat, c_lon = cluster_centroids[cluster_idx]
                else:
                    c_lat, c_lon = self.hotel_coords

                proximity_km = self._get_real_distance_km(
                    leftover["latitude"], leftover["longitude"], c_lat, c_lon
                )

                score = (-free_mins, proximity_km)
                if best_score is None or score < best_score:
                    best_score = score
                    best_day = day_idx

            if best_day is None:
                log.debug(
                    f"[Pass2] No room found for '{leftover['name']}' "
                    f"(bucket={leftover.get('bucket', 'want')}, "
                    f"dur={leftover.get('recommended_duration_mins', 120)} min) — excluded."
                )
                continue

            ctx = day_contexts[best_day]
            trial_pool = day_assigned_pois[best_day] + [leftover]
            nodes = self._build_node_list(trial_pool, ctx, ctx["end_node_coords"])
            trial_route = self._solve_day_route(
                nodes, ctx["start_min"], ctx["end_min"], transit_lookup
            )

            solved_in_trial = set()
            if trial_route and len(trial_route) >= 2:
                for step in trial_route[1:-1]:
                    n = step["node"]
                    if n["type"] == "attraction" and n["id"] != "lunch":
                        solved_in_trial.add(n["id"])

            if leftover["id"] not in solved_in_trial:
                log.debug(
                    f"[Pass2] Solver dropped '{leftover['name']}' from day {best_day} — skipping."
                )
                continue

            log.debug(
                f"[Pass2] Assigned '{leftover['name']}' "
                f"(bucket={leftover.get('bucket', 'want')}) to day {best_day}."
            )
            assigned_ids.add(leftover["id"])
            day_assigned_pois[best_day] = [
                n["node"]["poi_data"]
                for n in trial_route[1:-1]
                if n["node"]["type"] == "attraction" and n["node"]["id"] != "lunch"
            ]
            day_routes[best_day] = trial_route
            day_node_lists[best_day] = nodes

            old_entry = schedule_buffer[best_day]
            current_date = ctx["current_date"]
            base_dt = datetime.combine(current_date, time.min)
            wakeup_dt = ctx["wakeup_dt"]

            new_day_plan: List[Dict] = []

            if best_day == 0:
                bags_claim_end = self.arrival_dt + timedelta(
                    minutes=self.airport_egress_mins
                )
                new_day_plan.append(
                    {
                        "type": "attraction",
                        "id": "arr_airport",
                        "name": "Customs & Baggage Claim",
                        "bucket": "logistics",
                        "start_time": self.arrival_dt.strftime("%H:%M"),
                        "end_time": bags_claim_end.strftime("%H:%M"),
                        "transit_mins": 0,
                        "unknown_hours_warning": False,
                        "latitude": self.airport_coords[0],
                        "longitude": self.airport_coords[1],
                    }
                )
                est_arr_mins = self._get_base_transit_mins(
                    self.airport_coords[0],
                    self.airport_coords[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                )
                h_transit, h_leg = self._resolve_transit_leg(
                    self.airport_coords[0],
                    self.airport_coords[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    transit_lookup,
                    est_arr_mins,
                )
                hotel_arrival_time = bags_claim_end + timedelta(minutes=h_transit)
                checkin_end_time = hotel_arrival_time + timedelta(
                    minutes=self.hotel_checkin_mins
                )
                new_day_plan.append(
                    {
                        "type": "attraction",
                        "id": "arr_hotel",
                        "name": "Check-in & Settle at Hotel",
                        "bucket": "logistics",
                        "start_time": hotel_arrival_time.strftime("%H:%M"),
                        "end_time": checkin_end_time.strftime("%H:%M"),
                        "transit_mins": h_transit,
                        "unknown_hours_warning": False,
                        "latitude": self.hotel_coords[0],
                        "longitude": self.hotel_coords[1],
                        "transit_leg": h_leg,
                    }
                )

            route_events = self._build_route_events(
                best_day, total_days, ctx, trial_route, transit_lookup
            )
            new_day_plan.extend(route_events)

            schedule_buffer[best_day] = {
                "day_index": best_day,
                "date": current_date.strftime("%Y-%m-%d"),
                "events": new_day_plan,
            }

        schedule = [
            {k: v for k, v in schedule_buffer[d].items() if not k.startswith("_")}
            for d in active_days
            if schedule_buffer.get(d)
        ]

        excluded: Dict[str, List] = {"must": [], "want": [], "optional": []}
        for p in pois:
            if p["id"] not in assigned_ids:
                bucket = p.get("bucket", "optional").lower()
                if bucket not in excluded:
                    bucket = "optional"
                excluded[bucket].append(
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "bucket": bucket,
                        "type": "attraction",
                    }
                )

        return {"status": "success", "schedule": schedule, "excluded": excluded}

    def _is_open_interval(
        self, arrival_dt: datetime, departure_dt: datetime, opening_hours_str: Any
    ) -> tuple[bool, bool]:
        """
        Returns (is_open, is_unknown).
        Mirrors the same parsing logic as _get_time_window so that both methods
        handle bytes, "24/7", "24 hours", "null", "closed", etc. identically.
        Used only for generating the unknown_hours_warning flag on each event —
        it never affects scheduling decisions.
        """
        if not opening_hours_str:
            return True, True
        day_of_week = arrival_dt.strftime("%A").lower()
        try:
            if isinstance(opening_hours_str, bytes):
                opening_hours_str = opening_hours_str.decode("utf-8")
            if isinstance(opening_hours_str, str):
                hours_dict = json.loads(opening_hours_str)
            elif isinstance(opening_hours_str, dict):
                hours_dict = opening_hours_str
            else:
                return True, True

            day_hours = hours_dict.get(day_of_week)
            if day_hours is None or str(day_hours).lower() == "null":
                return True, True
            if "closed" in str(day_hours).lower():
                return False, False

            day_str = str(day_hours).lower().strip()
            if (
                "24/7" in day_str
                or "24 hours" in day_str
                or "00:00-24:00" in day_str
                or day_str == "24"
            ):
                return True, False

            if "-" in day_str:
                open_str, close_str = day_str.split("-", 1)
                open_t = datetime.strptime(open_str.strip(), "%H:%M").time()
                close_t = datetime.strptime(close_str.strip(), "%H:%M").time()

                open_min = open_t.hour * 60 + open_t.minute
                close_min = close_t.hour * 60 + close_t.minute

                if close_min < open_min:
                    close_min += 1440

                arrival_day_start = datetime.combine(arrival_dt.date(), time.min)
                arr_min = int((arrival_dt - arrival_day_start).total_seconds() / 60)
                dep_min = int((departure_dt - arrival_day_start).total_seconds() / 60)

                is_inside_window = (open_min <= arr_min) and (dep_min <= close_min)
                return is_inside_window, False

        except Exception as e:
            log.warning(f"_is_open_interval: failed to parse opening hours: {e}")
            return True, True

        return True, False

    def recalculate_user_timeline(
        self,
        user_days_poi_ids: List[List[int]],
        pois: List[Dict[str, Any]],
        existing_transit_legs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        poi_map = {p["id"]: p for p in pois}
        schedule = []
        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        transit_lookup = existing_transit_legs or {}

        _LOGISTICS_PREFIXES = ("start_", "return_", "arr_", "dep_", "transit_")

        def _is_logistics_id(pid) -> bool:
            return isinstance(pid, str) and any(
                pid.startswith(pfx) for pfx in _LOGISTICS_PREFIXES
            )

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
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    p["latitude"],
                    p["longitude"],
                )
                > CITY_DISTANCE_THRESHOLD_KM
                for p in real_pois_today
            )

            if is_excursion_day and real_pois_today:
                max_transit_mins = max(
                    self._get_base_transit_mins(
                        self.hotel_coords[0],
                        self.hotel_coords[1],
                        p["latitude"],
                        p["longitude"],
                    )
                    for p in real_pois_today
                )
                shift_mins = min(max_transit_mins, 120)
                earliest_allowed = datetime.combine(current_date, time(5, 0))
                wakeup_dt = max(
                    ideal_wakeup_dt - timedelta(minutes=shift_mins), earliest_allowed
                )

            elif day_idx == total_days - 1:
                est_dep_mins = self._get_base_transit_mins(
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    self.airport_coords[0],
                    self.airport_coords[1],
                )
                dep_transit_mins, _ = self._resolve_transit_leg(
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    self.airport_coords[0],
                    self.airport_coords[1],
                    transit_lookup,
                    est_dep_mins,
                )
                day_end_limit = self.departure_dt - timedelta(
                    minutes=self.pre_flight_buffer_mins
                )
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
                bags_claim_end = self.arrival_dt + timedelta(
                    minutes=self.airport_egress_mins
                )
                day_plan.append(
                    {
                        "type": "attraction",
                        "id": "arr_airport",
                        "name": "Customs & Baggage Claim",
                        "bucket": "logistics",
                        "start_time": self.arrival_dt.strftime("%H:%M"),
                        "end_time": bags_claim_end.strftime("%H:%M"),
                        "transit_mins": 0,
                        "unknown_hours_warning": False,
                        "latitude": self.airport_coords[0],
                        "longitude": self.airport_coords[1],
                    }
                )
                est_arr_mins = self._get_base_transit_mins(
                    self.airport_coords[0],
                    self.airport_coords[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                )
                h_transit, h_leg = self._resolve_transit_leg(
                    self.airport_coords[0],
                    self.airport_coords[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    transit_lookup,
                    est_arr_mins,
                )
                hotel_arrival_time = bags_claim_end + timedelta(minutes=h_transit)
                checkin_end_time = hotel_arrival_time + timedelta(
                    minutes=self.hotel_checkin_mins
                )
                day_plan.append(
                    {
                        "type": "attraction",
                        "id": "arr_hotel",
                        "name": "Check-in & Settle at Hotel",
                        "bucket": "logistics",
                        "start_time": hotel_arrival_time.strftime("%H:%M"),
                        "end_time": checkin_end_time.strftime("%H:%M"),
                        "transit_mins": h_transit,
                        "unknown_hours_warning": False,
                        "latitude": self.hotel_coords[0],
                        "longitude": self.hotel_coords[1],
                        "transit_leg": h_leg,
                    }
                )
                current_clock = max(checkin_end_time, ready_dt)

            else:
                current_clock = ready_dt

            if day_idx != 0:
                if first_real_poi is not None:
                    day_plan.append(
                        {
                            "type": "attraction",
                            "id": f"start_hotel_{day_idx}",
                            "name": "Start Day at Hotel",
                            "bucket": "logistics",
                            "start_time": wakeup_dt.strftime("%H:%M"),
                            "end_time": ready_dt.strftime("%H:%M"),
                            "transit_mins": 0,
                            "unknown_hours_warning": False,
                            "latitude": self.hotel_coords[0],
                            "longitude": self.hotel_coords[1],
                        }
                    )
                else:
                    day_plan.append(
                        {
                            "type": "attraction",
                            "id": f"start_hotel_{day_idx}",
                            "name": "Start Day at Hotel",
                            "bucket": "logistics",
                            "start_time": wakeup_dt.strftime("%H:%M"),
                            "end_time": ready_dt.strftime("%H:%M"),
                            "transit_mins": 0,
                            "unknown_hours_warning": False,
                            "latitude": self.hotel_coords[0],
                            "longitude": self.hotel_coords[1],
                        }
                    )
                    current_clock = ready_dt

            for poi_id in day_poi_ids:
                if _is_logistics_id(poi_id):
                    continue

                p = poi_map.get(poi_id)
                if not p:
                    continue

                if current_clock.hour >= 13 and not lunch_taken:
                    day_plan.append(
                        {
                            "type": "meal",
                            "name": "Lunch Break",
                            "start_time": current_clock.strftime("%H:%M"),
                            "end_time": (
                                current_clock
                                + timedelta(minutes=self.lunch_duration_mins)
                            ).strftime("%H:%M"),
                        }
                    )
                    current_clock += timedelta(minutes=self.lunch_duration_mins)
                    lunch_taken = True

                est_mins = self._get_base_transit_mins(
                    current_loc[0], current_loc[1], p["latitude"], p["longitude"]
                )
                final_transit_mins, transit_leg_state = self._resolve_transit_leg(
                    current_loc[0],
                    current_loc[1],
                    p["latitude"],
                    p["longitude"],
                    transit_lookup,
                    est_mins,
                )

                arr_dt = current_clock + timedelta(minutes=final_transit_mins)
                raw_dur = p.get("recommended_duration_mins", 120)
                dep_dt = arr_dt + timedelta(minutes=raw_dur)
                is_open, is_unk = self._is_open_interval(
                    arr_dt, dep_dt, p.get("opening_hours")
                )

                day_plan.append(
                    {
                        "type": "attraction",
                        "id": p["id"],
                        "name": p["name"],
                        "bucket": p.get("bucket", "want").lower(),
                        "start_time": arr_dt.strftime("%H:%M"),
                        "end_time": dep_dt.strftime("%H:%M"),
                        "transit_mins": final_transit_mins,
                        "unknown_hours_warning": not is_open if not is_unk else True,
                        "latitude": p["latitude"],
                        "longitude": p["longitude"],
                        "image_url": p.get("image_url"),
                        "transit_leg": transit_leg_state,
                    }
                )

                current_clock = dep_dt
                current_loc = (p["latitude"], p["longitude"])

            if day_idx != total_days - 1 and first_real_poi is not None:
                est_ret_mins = self._get_base_transit_mins(
                    current_loc[0],
                    current_loc[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                )
                ret_transit_mins, ret_leg = self._resolve_transit_leg(
                    current_loc[0],
                    current_loc[1],
                    self.hotel_coords[0],
                    self.hotel_coords[1],
                    transit_lookup,
                    est_ret_mins,
                )
                return_dt = current_clock + timedelta(minutes=ret_transit_mins)
                day_plan.append(
                    {
                        "type": "attraction",
                        "id": f"return_hotel_{day_idx}",
                        "name": "Return to Hotel",
                        "bucket": "logistics",
                        "start_time": return_dt.strftime("%H:%M"),
                        "end_time": return_dt.strftime("%H:%M"),
                        "transit_mins": ret_transit_mins,
                        "latitude": self.hotel_coords[0],
                        "longitude": self.hotel_coords[1],
                        "unknown_hours_warning": False,
                        "transit_leg": ret_leg,
                    }
                )
                current_clock = return_dt

            if day_idx == total_days - 1:
                airport_arrival_target = self.departure_dt - timedelta(
                    minutes=self.pre_flight_buffer_mins
                )
                est_dep_mins = self._get_base_transit_mins(
                    current_loc[0],
                    current_loc[1],
                    self.airport_coords[0],
                    self.airport_coords[1],
                )
                airport_transit_mins, dep_leg = self._resolve_transit_leg(
                    current_loc[0],
                    current_loc[1],
                    self.airport_coords[0],
                    self.airport_coords[1],
                    transit_lookup,
                    est_dep_mins,
                )
                leave_for_airport_dt = airport_arrival_target - timedelta(
                    minutes=airport_transit_mins
                )

                if current_clock < leave_for_airport_dt:
                    day_plan.append(
                        {
                            "type": "free_time",
                            "id": "free_time_hotel",
                            "name": "Relax / Prep for Departure",
                            "start_time": current_clock.strftime("%H:%M"),
                            "end_time": leave_for_airport_dt.strftime("%H:%M"),
                        }
                    )

                day_plan.append(
                    {
                        "type": "attraction",
                        "id": "dep_airport",
                        "name": "Airport Check-in & Security",
                        "bucket": "logistics",
                        "start_time": airport_arrival_target.strftime("%H:%M"),
                        "end_time": self.departure_dt.strftime("%H:%M"),
                        "transit_mins": airport_transit_mins,
                        "latitude": self.airport_coords[0],
                        "longitude": self.airport_coords[1],
                        "unknown_hours_warning": False,
                        "transit_leg": dep_leg,
                    }
                )

            schedule.append(
                {
                    "day_index": day_idx,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "events": day_plan,
                }
            )

        assigned_ids = set()
        for day in schedule:
            for event in day["events"]:
                if event.get("type") == "attraction" and "id" in event:
                    pid = event["id"]
                    if isinstance(pid, int) or (isinstance(pid, str) and pid.isdigit()):
                        assigned_ids.add(int(pid) if isinstance(pid, str) else pid)

        excluded = {"must": [], "want": [], "optional": []}

        for p in pois:
            if p["id"] not in assigned_ids:
                bucket = p.get("bucket", "optional").lower()
                if bucket not in excluded:
                    bucket = "optional"
                excluded[bucket].append(
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "bucket": bucket,
                        "type": "attraction",
                    }
                )

        return {"status": "success", "schedule": schedule, "excluded": excluded}

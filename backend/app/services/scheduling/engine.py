import numpy as np
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math
import logging

log = logging.getLogger(__name__)

class ScheduleEngine:
    def __init__(self, pace: str, arrival_dt: datetime, departure_dt: datetime):
        self.pace = pace.lower()
        self.arrival_dt = arrival_dt
        self.departure_dt = departure_dt
        
        # Base daily budgets based on Pace (in minutes)
        # We assume a standard "active" day is roughly 9 AM to 6 PM (9 hours = 540 mins)
        self.pace_mapping = {
            "relaxed": 5 * 60,   # 5 hours of active attractions
            "moderate": 7 * 60,  # 7 hours
            "fast-paced": 9 * 60 # 9 hours
        }
        self.base_daily_budget = self.pace_mapping.get(self.pace, 7 * 60)
        
        # Buffer added to each attraction to account for transit/walking
        self.transit_padding_mins = 30

    def _calculate_daily_budgets(self, total_days: int) -> List[int]:
        """
        Calculates the strict minute-budget for every day of the trip,
        heavily penalizing Day 1 (Arrival) and the Last Day (Departure).
        """
        budgets = [self.base_daily_budget] * total_days

        # --- DAY 1: ARRIVAL MATH ---
        hotel_arrival_time = self.arrival_dt + timedelta(hours=2)
        end_of_active_day = self.arrival_dt.replace(hour=19, minute=0)
        
        if hotel_arrival_time >= end_of_active_day:
            budgets[0] = 0
        else:
            available_mins = (end_of_active_day - hotel_arrival_time).total_seconds() / 60
            budgets[0] = min(available_mins, self.base_daily_budget)

        # --- LAST DAY: DEPARTURE MATH ---
        leave_for_airport_time = self.departure_dt - timedelta(hours=3)
        start_of_active_day = self.departure_dt.replace(hour=9, minute=0)
        
        if leave_for_airport_time <= start_of_active_day:
            budgets[-1] = 0
        else:
            available_mins = (leave_for_airport_time - start_of_active_day).total_seconds() / 60
            budgets[-1] = min(available_mins, self.base_daily_budget)

        return budgets

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Simple Euclidean distance for fast comparative sorting (Haversine not strictly needed here)"""
        return (lat1 - lat2)**2 + (lon1 - lon2)**2

    def generate_initial_draft(self, pois: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        The main orchestrator: Clusters POIs geographically, then balances them temporally.
        """
        if not pois:
            return {}

        total_days = (self.departure_dt.date() - self.arrival_dt.date()).days + 1
        budgets = self._calculate_daily_budgets(total_days)
        
        # Identify days that actually have enough time to do things
        active_day_indices = [i for i, b in enumerate(budgets) if b > 60]
        
        if not active_day_indices:
            return {"status": "error", "message": "Trip is too short to schedule attractions."}

        num_clusters = min(len(active_day_indices), len(pois)) 

        # 1. Geographic Clustering via K-Means
        coords = np.array([[poi['latitude'], poi['longitude']] for poi in pois])
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
        kmeans.fit(coords)
        
        # Map K-Means labels (0, 1, 2) to actual chronological day indices
        cluster_to_day = {i: active_day_indices[i] for i in range(num_clusters)}

        for i, poi in enumerate(pois):
            poi['assigned_day'] = cluster_to_day[int(kmeans.labels_[i])]

        # 2. Time-Spillover Balancing (The Knapsack Adjustment)
        max_iterations = 50 # Safety break for the while loop
        
        for iteration in range(max_iterations):
            moved_any_poi = False
            
            # Calculate current time load for each day
            day_loads = {day_idx: 0 for day_idx in active_day_indices}
            day_pois = {day_idx: [] for day_idx in active_day_indices}
            
            for poi in pois:
                day = poi['assigned_day']
                duration = poi.get('recommended_duration_mins', 120)
                padded_time = duration + self.transit_padding_mins
                
                day_loads[day] += padded_time
                day_pois[day].append(poi)
                
            # Identify which days exceed their allocated time budget
            overloaded_days = [d for d in active_day_indices if day_loads[d] > budgets[d]]
            
            if not overloaded_days:
                log.info(f"Balanced perfectly in {iteration} iterations.")
                break # Schedule is fully balanced!
                
            for over_day in overloaded_days:
                over_pois = day_pois[over_day]
                if len(over_pois) <= 1:
                    continue # Cannot empty a day entirely
                    
                # Find the geographic center of this specific day's attractions
                center_lat = sum(p['latitude'] for p in over_pois) / len(over_pois)
                center_lon = sum(p['longitude'] for p in over_pois) / len(over_pois)
                
                # Find the "Outlier" - the POI furthest from this day's center
                furthest_poi = None
                max_dist = -1
                for p in over_pois:
                    dist = self._calculate_distance(p['latitude'], p['longitude'], center_lat, center_lon)
                    if dist > max_dist:
                        max_dist = dist
                        furthest_poi = p
                
                poi_time_cost = furthest_poi.get('recommended_duration_mins', 120) + self.transit_padding_mins
                
                # Look for the nearest day that has spare capacity
                best_alt_day = None
                min_alt_dist = float('inf')
                
                for alt_day in active_day_indices:
                    if alt_day == over_day:
                        continue
                        
                    if day_loads[alt_day] + poi_time_cost <= budgets[alt_day]:
                        alt_pois = day_pois[alt_day]
                        if not alt_pois:
                            alt_dist = 0 # Empty day, perfect to dump into
                        else:
                            alt_center_lat = sum(p['latitude'] for p in alt_pois) / len(alt_pois)
                            alt_center_lon = sum(p['longitude'] for p in alt_pois) / len(alt_pois)
                            alt_dist = self._calculate_distance(
                                furthest_poi['latitude'], furthest_poi['longitude'], 
                                alt_center_lat, alt_center_lon
                            )
                            
                        if alt_dist < min_alt_dist:
                            min_alt_dist = alt_dist
                            best_alt_day = alt_day
                            
                # Reassign the outlier to the best alternative day
                if best_alt_day is not None:
                    furthest_poi['assigned_day'] = best_alt_day
                    moved_any_poi = True
                    break # Break out to recalculate all loads with the new configuration
                    
            if not moved_any_poi:
                # If we get here, days are overloaded but NO other days have spare capacity.
                # The user simply selected too many attractions for their pace/trip length.
                log.warning("Schedule is oversaturated. Attaching 'packed_schedule' flag.")
                return {
                    "status": "success",
                    "warning": "packed_schedule",
                    "budgets": budgets,
                    "draft_pois": pois
                }

        # Final sort: ensure POIs within each day are ordered in a logical geographical line
        self._sort_pois_internally(pois, active_day_indices)

        return {
            "status": "success",
            "warning": None,
            "budgets": budgets,
            "draft_pois": pois
        }

    def _sort_pois_internally(self, pois: List[Dict[str, Any]], active_day_indices: List[int]):
        """
        A basic Greedy Nearest Neighbor sort so the list order within each day makes sense
        """
        for day in active_day_indices:
            day_items = [p for p in pois if p['assigned_day'] == day]
            if not day_items:
                continue
                
            # Start with the northernmost attraction (simple heuristic for a starting point)
            day_items.sort(key=lambda x: x['latitude'], reverse=True)
            ordered = [day_items.pop(0)]
            
            while day_items:
                last_poi = ordered[-1]
                # Find the closest next point
                closest_idx = min(
                    range(len(day_items)), 
                    key=lambda i: self._calculate_distance(
                        last_poi['latitude'], last_poi['longitude'],
                        day_items[i]['latitude'], day_items[i]['longitude']
                    )
                )
                ordered.append(day_items.pop(closest_idx))
                
            # Re-insert into original list with an explicit 'day_order' key
            for order_idx, ordered_poi in enumerate(ordered):
                for p in pois:
                    if p['id'] == ordered_poi['id']:
                        p['day_order'] = order_idx
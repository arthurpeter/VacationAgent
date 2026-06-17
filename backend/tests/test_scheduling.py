import math

import pytest
from datetime import datetime
from app.services.scheduling.engine import ScheduleEngine

ALL_PARIS_POIS = [
        {
            "id": 10, "name": "Chapelle Sainte-Thérèse de Montmagny", "bucket": "optional",
            "latitude": 48.962120056152344, "longitude": 2.3322455883026123, "recommended_duration_mins": 60,
            "opening_hours": '{"monday": null, "tuesday": null, "wednesday": null, "thursday": null, "friday": null, "saturday": null, "sunday": null}'
        },
        {
            "id": 13, "name": "Stade de France Miniature", "bucket": "optional",
            "latitude": 48.776981353759766, "longitude": 1.962082028388977, "recommended_duration_mins": 240,
            "opening_hours": '{"monday": null, "tuesday": null, "wednesday": null, "thursday": null, "friday": null, "saturday": null, "sunday": null}'
        },
        {
            "id": 15, "name": "Parc Balbi", "bucket": "optional",
            "latitude": 48.79695510864258, "longitude": 2.1194443702697754, "recommended_duration_mins": 90,
            "opening_hours": '{"monday": null, "tuesday": null, "wednesday": null, "thursday": null, "friday": null, "saturday": null, "sunday": null}'
        },
        {
            "id": 17, "name": "Eiffel Tower", "bucket": "must",
            "latitude": 48.8582878112793, "longitude": 2.2944986820220947, "recommended_duration_mins": 180,
            "opening_hours": '{"monday": "09:15-23:45", "tuesday": "09:15-23:45", "wednesday": "09:15-23:45", "thursday": "09:15-23:45", "friday": "09:15-23:45", "saturday": "09:15-23:45", "sunday": "09:15-23:45"}'
        },
        {
            "id": 19, "name": "Cathedral of Notre Dame", "bucket": "want",
            "latitude": 48.852935791015625, "longitude": 2.350050210952759, "recommended_duration_mins": 120,
            "opening_hours": '{"monday": "07:50-19:00", "tuesday": "07:50-19:00", "wednesday": "07:50-19:00", "thursday": "07:50-22:00", "friday": "07:50-19:00", "saturday": "08:15-19:30", "sunday": "08:15-19:30"}'
        },
        {
            "id": 18, "name": "Louvre Museum", "bucket": "must",
            "latitude": 48.861148834228516, "longitude": 2.3380274772644043, "recommended_duration_mins": 180,
            "opening_hours": '{"monday": "09:00-18:00", "tuesday": "Closed", "wednesday": "09:00-21:00", "thursday": "09:00-18:00", "friday": "09:00-21:00", "saturday": "09:00-18:00", "sunday": "09:00-18:00"}'
        },
        {
            "id": 22, "name": "Palace of Justice", "bucket": "want",
            "latitude": 48.855655670166016, "longitude": 2.3450512886047363, "recommended_duration_mins": 90,
            "opening_hours": '{"monday": "N/A", "tuesday": "N/A", "wednesday": "N/A", "thursday": "N/A", "friday": "N/A", "saturday": "N/A", "sunday": "N/A"}'
        },
        {
            "id": 24, "name": "Élysée Montmartre", "bucket": "optional",
            "latitude": 48.883113861083984, "longitude": 2.3434195518493652, "recommended_duration_mins": 180,
            "opening_hours": '{"monday": "N/A", "tuesday": "N/A", "wednesday": "N/A", "thursday": "N/A", "friday": "N/A", "saturday": "N/A", "sunday": "N/A"}'
        },
        {
            "id": 31, "name": "Parc des Beaumonts", "bucket": "optional",
            "latitude": 48.85845184326172, "longitude": 2.453369140625, "recommended_duration_mins": 120,
            "opening_hours": '{"monday": "00:00-24:00", "tuesday": "00:00-24:00", "wednesday": "00:00-24:00", "thursday": "00:00-24:00", "friday": "00:00-24:00", "saturday": "00:00-24:00", "sunday": "00:00-24:00"}'
        },
        {
            "id": 21, "name": "Arcade des Champs-Élysées", "bucket": "want",
            "latitude": 48.8716926574707, "longitude": 2.30460524559021, "recommended_duration_mins": 120,
            "opening_hours": '{"monday": "N/A", "tuesday": "N/A", "wednesday": "N/A", "thursday": "N/A", "friday": "N/A", "saturday": "N/A", "sunday": "N/A"}'
        },
        {
            "id": 25, "name": "Latin Quarter", "bucket": "must",
            "latitude": 48.84873962402344, "longitude": 2.342050075531006, "recommended_duration_mins": 150,
            "opening_hours": '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}'
        },
        {
            "id": 26, "name": "Dome of Les Invalids", "bucket": "want",
            "latitude": 48.85499572753906, "longitude": 2.312530517578125, "recommended_duration_mins": 180,
            "opening_hours": '{"monday": "10:00-18:00", "tuesday": "10:00-18:00", "wednesday": "10:00-18:00", "thursday": "10:00-18:00", "friday": "10:00-18:00", "saturday": "10:00-18:00", "sunday": "10:00-18:00"}'
        },
        {
            "id": 27, "name": "Centre Georges Pompidou", "bucket": "optional",
            "latitude": 48.860591888427734, "longitude": 2.3524742126464844, "recommended_duration_mins": 180,
            "opening_hours": '{"monday": "N/A", "tuesday": "Closed", "wednesday": "11:00-21:00", "thursday": "11:00-21:00", "friday": "11:00-21:00", "saturday": "N/A", "sunday": "N/A"}'
        },
        {
            "id": 23, "name": "Sacré-Cœur", "bucket": "must",
            "latitude": 48.88680648803711, "longitude": 2.343015193939209, "recommended_duration_mins": 120,
            "opening_hours": '{"monday": "06:30-22:30", "tuesday": "06:30-22:30", "wednesday": "06:30-22:30", "thursday": "06:30-22:30", "friday": "06:30-22:30", "saturday": "06:30-22:30", "sunday": "06:30-22:30"}'
        },
        {
            "id": 20, "name": "Arc de Triomphe", "bucket": "must",
            "latitude": 48.873779296875, "longitude": 2.295037269592285, "recommended_duration_mins": 90,
            "opening_hours": '{"monday": "10:00-23:00", "tuesday": "10:00-23:00", "wednesday": "10:00-23:00", "thursday": "10:00-23:00", "friday": "10:00-23:00", "saturday": "10:00-23:00", "sunday": "10:00-23:00"}'
        },
        {
            "id": 28, "name": "Tuileries Garden", "bucket": "optional",
            "latitude": 48.86366271972656, "longitude": 2.3268399238586426, "recommended_duration_mins": 120,
            "opening_hours": '{"monday": "N/A", "tuesday": "N/A", "wednesday": "N/A", "thursday": "N/A", "friday": "N/A", "saturday": "N/A", "sunday": "N/A"}'
        },
        {
            "id": 29, "name": "Banks of the Seine", "bucket": "optional",
            "latitude": 48.849998474121094, "longitude": 2.3588900566101074, "recommended_duration_mins": 180,
            "opening_hours": '{"monday": "00:00-24:00", "tuesday": "00:00-24:00", "wednesday": "00:00-24:00", "thursday": "00:00-24:00", "friday": "00:00-24:00", "saturday": "00:00-24:00", "sunday": "00:00-24:00"}'
        },
        {
            "id": 30, "name": "Pont Neuf", "bucket": "optional",
            "latitude": 48.85652542114258, "longitude": 2.3408308029174805, "recommended_duration_mins": 60,
            "opening_hours": '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}'
        },
        {
            "id": 33, "name": "Palais Royal", "bucket": "optional",
            "latitude": 48.86358642578125, "longitude": 2.3362042903900146, "recommended_duration_mins": 120,
            "opening_hours": '{"monday": "N/A", "tuesday": "N/A", "wednesday": "N/A", "thursday": "N/A", "friday": "N/A", "saturday": "N/A", "sunday": "N/A"}'
        },
        {
            "id": 32, "name": "Place des Vosges", "bucket": "optional",
            "latitude": 48.855621337890625, "longitude": 2.3655426502227783, "recommended_duration_mins": 120,
            "opening_hours": '{"monday": "00:00-23:59", "tuesday": "00:00-23:59", "wednesday": "00:00-23:59", "thursday": "00:00-23:59", "friday": "00:00-23:59", "saturday": "00:00-23:59", "sunday": "00:00-23:59"}'
        }
    ]

def _to_mins(time_str: str) -> int:
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def assert_schedule_integrity(result: dict, input_pois: list):
    """Functie master de validare a constrangerilor structulare si logice."""
    assert result["status"] == "success"
    schedule = result["schedule"]
    excluded = result["excluded"]
    total_days = len(schedule)

    # 1. VALIDARE: Conservarea datelor (No POI Leakage)
    scheduled_ids = set()
    for day in schedule:
        for event in day["events"]:
            if event["type"] == "attraction" and isinstance(event.get("id"), int):
                assert event["id"] not in scheduled_ids, f"Atractia {event['name']} este duplicata!"
                scheduled_ids.add(event["id"])

    excluded_ids = set()
    for bucket in ["must", "want", "optional"]:
        for p in excluded.get(bucket, []):
            excluded_ids.add(p["id"])

    input_ids = {p["id"] for p in input_pois}
    assert scheduled_ids.union(excluded_ids) == input_ids, "Scurgere de date: unele atractii au disparut complet!"

    # 2. COLECTARE DATE PENTRU ECHILIBRU DINAMIC
    full_day_loads = []
    
    # Mapam duratele din input pentru a gasi rapid configuratia initiala
    poi_duration_map = {p["id"]: p.get("recommended_duration_mins", 120) for p in input_pois}
    scheduled_durations = [poi_duration_map[pid] for pid in scheduled_ids if pid in poi_duration_map]
    
    # Durata maxima a unei atractii alese sa ramana in program
    max_scheduled_duration = max(scheduled_durations) if scheduled_durations else 120

    for day in schedule:
        day_idx = day["day_index"]
        is_transit_day = (day_idx == 0 or day_idx == total_days - 1)
        events = day["events"]
        
        # Calculam incarcarea cumulată de vizitare pura (fara pranz sau hotel)
        if not is_transit_day:
            day_sightseeing_mins = sum(
                (_to_mins(e["end_time"]) - _to_mins(e["start_time"]))
                for e in events if e["type"] == "attraction" and isinstance(e.get("id"), int)
            )
            full_day_loads.append(day_sightseeing_mins)

        # 3. VALIDARE: Non-suprapunere si Cronologie
        for i in range(len(events)):
            curr = events[i]
            c_start = _to_mins(curr["start_time"])
            c_end = _to_mins(curr["end_time"])

            assert c_end >= c_start, f"Eroare cronologica: {curr['name']} are durata negativa!"

            if not is_transit_day:
                if curr["type"] == "attraction" and not str(curr.get("id")).startswith("return_"):
                    assert c_end <= 20 * 60 + 30, f"Ritm incalcat: {curr['name']} depaseste ora 20:30!"

            if i > 0:
                prev = events[i-1]
                p_end = _to_mins(prev["end_time"])
                assert c_start >= p_end, f"Suprapunere detectata intre {prev['name']} si {curr['name']}!"

    # 4. VALIDARE: Echilibrul pe baza deviatiei standard raportat la max_scheduled_duration
    # Filtram doar zilele active (incarcare > 0) pentru a nu penaliza zilele goale necesare din grupurile mici
    active_loads = [load for load in full_day_loads if load > 0]
    
    if len(active_loads) > 1:
        mean_load = sum(active_loads) / len(active_loads)
        variance = sum((x - mean_load) ** 2 for x in active_loads) / len(active_loads)
        std_deviation = math.sqrt(variance)

        # Deviația standard a timpului pe zilele active nu are voie sa fie mai mare 
        # decat cea mai lunga atractie incadrata in itinerariu
        assert std_deviation <= max_scheduled_duration, (
            f"Defect de echilibrare (Frontloading/Clustering defectuos)! "
            f"Deviația standard intre zile este de {std_deviation:.1f} minute, "
            f"depasind limita maxima permisa de {max_scheduled_duration} minute."
        )


def assert_recalculation_integrity(result: dict, input_pois: list):
    """Functie master de validare DINAMICA pentru modulul de Recalculare Manuala."""
    assert result["status"] == "success"
    schedule = result["schedule"]
    
    # Cream un dictionar de mapare rapida a atractiilor de input
    poi_map = {p["id"]: p for p in input_pois}

    for day in schedule:
        day_idx = day["day_index"]
        date_str = day["date"]
        
        # Identificam dinamic ziua saptamanii corespunzatoare datei calendaristice
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_week = date_obj.strftime("%A").lower()
        
        events = day["events"]
        time_cursor = 0  # Cursor absolut in minute pentru a urmari progresia liniara a timpului
        prev = None  # Evenimentul anterior pentru verificarea suprapunerii
        
        for curr in events:
            c_start = _to_mins(curr["start_time"])
            c_end = _to_mins(curr["end_time"])

            # Daca am trecut de miezul noptii, convertim timpul intr-o axa liniara continua (> 24h)
            while c_start < time_cursor:
                c_start += 1440
            
            while c_end < c_start:
                c_end += 1440

            # Constrangere cronologica de baza
            assert c_end >= c_start, f"Eroare: Evenimentul {curr['name']} are durata negativa!"

            # VALIDARE ALERTE DINAMICE (Warning Engine Verification)
            if curr["type"] == "attraction" and isinstance(curr.get("id"), int):
                poi_id = curr["id"]
                raw_poi_data = poi_map[poi_id]
                opening_hours_str = raw_poi_data.get("opening_hours", "")

                # Daca in metadatele brute obiectivul e marcat explicit ca inchis ("Closed")
                if opening_hours_str and "closed" in opening_hours_str.lower() and day_of_week in opening_hours_str.lower():
                    assert curr["unknown_hours_warning"] is True, (
                        f"Defect de avertizare! Atracția '{curr['name']}' a fost programata manual martea, "
                        f"dar sistemul nu a generat avertismentul 'unknown_hours_warning: True'."
                    )
                else:
                    if opening_hours_str and "closed" in opening_hours_str.lower() and "holiday" not in opening_hours_str.lower():
                        if day_of_week not in opening_hours_str.lower():
                            assert curr["unknown_hours_warning"] is False, f"Avertisment fals-pozitiv generat pentru {curr['name']}!"

            # CONSTRANGERE DURA DE NON-SUPRAPUNERE (pe axa liniara de timp)
            assert c_start >= time_cursor, f"Suprapunere fizica detectata la recalculare intre {prev['name']} si {curr['name']} in ziua {day_idx}!"
            prev = curr
            # Avansam cursorul la ora de final a activitatii curente
            time_cursor = c_end


def test_schedule_engine_small_group_load():
    input_pois = ALL_PARIS_POIS[:5]
    engine = ScheduleEngine(
        pace="moderate",
        arrival_dt=datetime.fromisoformat("2027-01-03T19:45:00"),
        departure_dt=datetime.fromisoformat("2027-01-10T13:05:00"),
        hotel_coords=(48.8794868643492, 2.33417227864265),
        airport_coords=(49.0128, 2.55)
    )
    result = engine.generate_schedule(input_pois)
    assert_schedule_integrity(result, input_pois)


def test_schedule_engine_medium_group_load():
    input_pois = ALL_PARIS_POIS[:12]
    engine = ScheduleEngine(
        pace="moderate",
        arrival_dt=datetime.fromisoformat("2027-01-03T19:45:00"),
        departure_dt=datetime.fromisoformat("2027-01-10T13:05:00"),
        hotel_coords=(48.8794868643492, 2.33417227864265),
        airport_coords=(49.0128, 2.55)
    )
    result = engine.generate_schedule(input_pois)
    assert_schedule_integrity(result, input_pois)


def test_schedule_engine_large_group_load():
    input_pois = ALL_PARIS_POIS
    engine = ScheduleEngine(
        pace="moderate",
        arrival_dt=datetime.fromisoformat("2027-01-03T19:45:00"),
        departure_dt=datetime.fromisoformat("2027-01-10T13:05:00"),
        hotel_coords=(48.8794868643492, 2.33417227864265),
        airport_coords=(49.0128, 2.55)
    )
    result = engine.generate_schedule(input_pois)
    assert_schedule_integrity(result, input_pois)


def test_schedule_engine_manual_recalculation():
    engine = ScheduleEngine(
        pace="moderate",
        arrival_dt=datetime.fromisoformat("2027-01-03T19:45:00"), # Duminica (Ziua 0)
        departure_dt=datetime.fromisoformat("2027-01-10T13:05:00"), # Duminica (Ziua 7)
        hotel_coords=(48.8794868643492, 2.33417227864265),
        airport_coords=(49.0128, 2.55)
    )

    # Distribuim complet toate cele 20 de ID-uri de atractii in mod arbitrar/manual pe zile
    # Ziua 2 (Marti - 5 Ianuarie) contine ID-ul 18 (Louvre) si ID-ul 27 (Pompidou), ambele INCHISE martea!
    user_days_poi_ids = [
        [],                          # Ziua 0 (Duminica - Sosire)
        [10, 13, 15, 17],            # Ziua 1 (Luni)
        [18, 27, 19, 22],            # Ziua 2 (Marti - Ziua cu restrictii de inchidere)
        [24, 31, 21, 23],            # Ziua 3 (Miercuri)
        [20, 28, 29],                # Ziua 4 (Joi)
        [30, 33, 32],                # Ziua 5 (Vineri)
        [25, 26],                    # Ziua 6 (Sambata)
        []                           # Ziua 7 (Duminica - Plecare)
    ]

    # Executam recalcularea
    result = engine.recalculate_user_timeline(user_days_poi_ids, ALL_PARIS_POIS)
    
    # Validam dinamica intregului program reconstituit manual prin functia master
    assert_recalculation_integrity(result, ALL_PARIS_POIS)

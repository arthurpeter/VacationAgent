from app.services.search import flights, accomodations_v2, explore
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from authx import TokenPayload
from app.core.auth import access_token_header
from datetime import datetime
from urllib.parse import parse_qs, urlparse, urlencode, parse_qsl, urlunparse
from app.core.airport_data import AIRPORTS_DB


log = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/airports/autocomplete")
def search_airports_autocomplete(q: str = Query(..., min_length=2)):
    query = q.lower().strip()
    matches = []
    
    for code, data in AIRPORTS_DB.items():
        city = data.get('city', '').lower()
        name = data.get('name', '').lower()
        code_lower = code.lower()
        
        if query in city or query in name or query in code_lower:
            
            if code_lower.startswith(query):
                score = 0
                
            elif query == city:
                if "international" in name or "intl" in name:
                    score = 10
                elif "municipal" in name or "county" in name or "field" in name:
                    score = 30
                else:
                    score = 20
                    
            elif city.startswith(query):
                score = 40
                
            elif name.startswith(query):
                score = 50
                
            elif query in city:
                score = 60
                
            else:
                score = 70
                
            matches.append((score, {
                "code": code,
                "city": data.get('city', ''),
                "name": data.get('name', ''),
                "country": data.get('country', '')
            }))
            
    matches.sort(key=lambda x: (x[0], x[1]['country'], x[1]['city']))

    # log.debug(f"Autocomplete search for '{q}' found {len(matches)} matches. Returning top 15.")
    
    results = [m[1] for m in matches[:15]]
            
    return results

# example usage of the explore api - currently disabled
# @router.post("/exploreDestinations", response_model=schemas.ExploreResponse)
# async def explore_destinations(data: schemas.ExploreRequest):
#     log.info(f"Exploring dates from {data.departure} to {data.arrival}")
#     try:
#         departure = data.departure.split(",")
#         city = departure[0].strip()
#         country = departure[1].strip() if len(departure) > 1 else None
#         results = flights.get_location_data(city, country)

#         arrival = data.arrival.split(",")
#         city = arrival[0].strip()
#         country = arrival[1].strip() if len(arrival) > 1 else None
#         arrival_id = flights.get_location_data(city, country).get("departure_id")
#     except Exception as e:
#         log.error(f"Error getting flight parameters: {e}")

#     log.info("Searching for explore destinations...")
#     explore_results = explore.call_explore_api(
#         departure_id=results.get("departure_id"),
#         arrival_id=arrival_id,
#         travel_duration=data.duration_type,
#         month=data.month,
#         adults=data.adults,
#         children=data.children,
#         infants_in_seat=data.infants_in_seat,
#         infants_on_lap=data.infants_on_lap,
#         stops=data.stops,
#         gl=results.get("gl"),
#         hl=results.get("hl"),
#         currency=results.get("currency")
#     )

#     if not explore_results:
#         log.warning("No explore destinations found for the given criteria.")
#         raise HTTPException(status_code=404, detail="No explore destinations found")
    
#     response = schemas.ExploreResponse(
#         start_date=explore_results.get("start_date"),
#         end_date=explore_results.get("end_date")
#     )

#     if not response.start_date or not response.end_date:
#         log.error("Error constructing explore response: Incomplete data received.")
#         raise HTTPException(status_code=500, detail="Error processing explore data")
#     return response

@router.post("/getOutboundFlights", response_model=list[schemas.FlightsResponse])
async def search_outbound_flights(
    data: schemas.FlightsRequest,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Searching flights: {data.departure} -> {data.arrival}")
    try:
        departure_codes = [c.strip().upper() for c in data.departure.split(",") if c.strip()]
        is_departure_iata = len(departure_codes) > 0 and all(len(c) == 3 and c in AIRPORTS_DB for c in departure_codes)

        if is_departure_iata:
            first_airport = AIRPORTS_DB[departure_codes[0]]
            stmt = select(models.VacationSession).filter(
                models.VacationSession.id == data.session_id,
                models.VacationSession.user_id == access_token.sub
            )
            result = await db.execute(stmt)
            session = result.scalars().first()
            currency = (session.currency if session else "EUR") or "EUR"
            results = {
                "departure_id": ",".join(departure_codes),
                "gl": first_airport.get('country', 'US').lower(),
                "hl": "en",
                "currency": currency
            }
            log.info(f"Location data for departure {', '.join(departure_codes)}: {results}")
        else:
            departure = data.departure.split(",")
            city = departure[0].strip()
            country = departure[1].strip() if len(departure) > 1 else None
            results = flights.get_location_data(city, country)

            log.info(f"Location data for departure {city}, {country}: {results}")

        arrival_codes = [c.strip().upper() for c in data.arrival.split(",") if c.strip()]
        is_arrival_iata = len(arrival_codes) > 0 and all(len(c) == 3 and c in AIRPORTS_DB for c in arrival_codes)

        if is_arrival_iata:
            arrival_id = ",".join(arrival_codes)
        else:
            arrival = data.arrival.split(",")
            city = arrival[0].strip()
            country = arrival[1].strip() if len(arrival) > 1 else None
            arrival_id = flights.get_location_data(city, country).get("departure_id")

        log.info(f"Location data for arrival {city}, {country}: {arrival_id}")

        if not results.get("departure_id"):
             raise HTTPException(status_code=400, detail=f"Could not find airports for origin: {data.departure}")
        
        if not arrival_id:
             raise HTTPException(status_code=400, detail=f"Could not find airports for destination: {data.arrival}. Please try a specific city name.")

    except Exception as e:
        log.error(f"Error getting flight parameters: {e}")
        raise HTTPException(status_code=400, detail="Invalid location format")

    log.info("Searching for outbound flights...")
    flight_results = flights.call_flights_api(
        departure_id=results.get("departure_id"),
        arrival_id=arrival_id,
        outbound_date=data.outbound_date,
        return_date=data.return_date,
        adults=data.adults,
        children=data.children,
        infants_in_seat=data.infants_in_seat,
        infants_on_lap=data.infants_on_lap,
        sort_by=data.sort_by,
        stops=data.stops,
        gl=results.get("gl"),
        hl=results.get("hl"),
        currency=results.get("currency")
    )

    best_flights = flight_results.get("best_flights")
    other_flights = flight_results.get("other_flights")
    all_flights = (best_flights or []) + (other_flights or [])

    if not all_flights:
        log.warning("No flights found for the given criteria.")
        raise HTTPException(status_code=404, detail="No flights found")
    
    log.info(f"Found {len(all_flights)} flights.")
    try:
        response = []
        for flight in all_flights[:12]:
            log.info(f"Flight: Price {flight.get('price')}")
            if not flight.get('departure_token'):
                log.warning("Skipping flight with missing departure token.")
                continue
            flight_schema = schemas.FlightsResponse(
                token=flight.get('departure_token'),
                price=flight.get('price'),
                currency=results.get("currency", "EUR"),
                flights=[]
            )
            for detail in flight.get('flights', []):
                flight_detail = schemas.Flight(
                    airline=detail.get('airline', ''),
                    airline_logo=detail.get('airline_logo'),
                    departure=detail.get('departure_airport', {}).get('name'),
                    departure_time=detail.get('departure_airport', {}).get('time'),
                    arrival=detail.get('arrival_airport', {}).get('name'),
                    arrival_time=detail.get('arrival_airport', {}).get('time'),
                    duration=str(detail.get('duration', '')),
                    airplane=detail.get('airplane'),
                    travel_class=detail.get('travel_class'),
                    extensions=[ext for ext in detail.get('extensions', [])]
                )
                flight_schema.flights.append(flight_detail)
            response.append(flight_schema)
    except Exception as e:
        log.error(f"Error constructing flight response: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing flight data: {e}")
        
    return response

@router.post("/getInboundFlights", response_model=list[schemas.FlightsResponse])
async def search_inbound_flights(
    data: schemas.FlightsRequest,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Searching flight: {data.departure} -> {data.arrival}")
    try:
        departure_codes = [c.strip().upper() for c in data.departure.split(",") if c.strip()]
        is_departure_iata = len(departure_codes) > 0 and all(len(c) == 3 and c in AIRPORTS_DB for c in departure_codes)

        if is_departure_iata:
            first_airport = AIRPORTS_DB[departure_codes[0]]
            stmt = select(models.VacationSession).filter(
                models.VacationSession.id == data.session_id,
                models.VacationSession.user_id == access_token.sub
            )
            result = await db.execute(stmt)
            session = result.scalars().first()
            currency = (session.currency if session else "EUR") or "EUR"
            results = {
                "departure_id": ",".join(departure_codes),
                "gl": first_airport.get('country', 'US').lower(),
                "hl": "en",
                "currency": currency
            }
        else:
            departure = data.departure.split(",")
            city = departure[0].strip()
            country = departure[1].strip() if len(departure) > 1 else None
            results = flights.get_location_data(city, country)

        arrival_codes = [c.strip().upper() for c in data.arrival.split(",") if c.strip()]
        is_arrival_iata = len(arrival_codes) > 0 and all(len(c) == 3 and c in AIRPORTS_DB for c in arrival_codes)

        if is_arrival_iata:
            arrival_id = ",".join(arrival_codes)
        else:
            arrival = data.arrival.split(",")
            city = arrival[0].strip()
            country = arrival[1].strip() if len(arrival) > 1 else None
            arrival_id = flights.get_location_data(city, country).get("departure_id")

        if not results.get("departure_id"):
             raise HTTPException(status_code=400, detail=f"Could not find airports for origin: {data.departure}")
        
        if not arrival_id:
             raise HTTPException(status_code=400, detail=f"Could not find airports for destination: {data.arrival}")
    except Exception as e:
        log.error(f"Error getting flight parameters: {e}")
        raise HTTPException(status_code=400, detail="Invalid location format")

    log.info("Searching for inbound flights...")
    flight_results = flights.call_flights_api(
        departure_token=data.token,
        departure_id=results.get("departure_id"),
        arrival_id=arrival_id,
        outbound_date=data.outbound_date,
        return_date=data.return_date,
        adults=data.adults,
        children=data.children,
        infants_in_seat=data.infants_in_seat,
        infants_on_lap=data.infants_on_lap,
        sort_by=data.sort_by,
        stops=data.stops,
        gl=results.get("gl"),
        hl=results.get("hl"),
        currency=results.get("currency", "EUR")
    )

    best_flights = flight_results.get("best_flights")
    other_flights = flight_results.get("other_flights")
    all_flights = (best_flights or []) + (other_flights or [])

    if not all_flights:
        log.warning("No flights found for the given criteria.")
        raise HTTPException(status_code=404, detail="No flights found")
    
    log.info(f"Found {len(all_flights)} flights.")
    try:
        response = []
        for flight in all_flights[:12]:
            log.info(f"Flight: Price {flight.get('price')}")
            if not flight.get('booking_token'):
                log.warning("Skipping flight with missing booking token.")
                continue
            flight_schema = schemas.FlightsResponse(
                token=flight.get('booking_token'),
                price=flight.get('price'),
                currency=results.get("currency"),
                flights=[]
            )
            for detail in flight.get('flights', []):
                flight_detail = schemas.Flight(
                    airline=detail.get('airline', ''),
                    airline_logo=detail.get('airline_logo'),
                    departure=detail.get('departure_airport', {}).get('name'),
                    departure_time=detail.get('departure_airport', {}).get('time'),
                    arrival=detail.get('arrival_airport', {}).get('name'),
                    arrival_time=detail.get('arrival_airport', {}).get('time'),
                    duration=str(detail.get('duration', '')),
                    airplane=detail.get('airplane'),
                    travel_class=detail.get('travel_class'),
                    extensions=[ext for ext in detail.get('extensions', [])]
                )
                flight_schema.flights.append(flight_detail)
            response.append(flight_schema)
    except Exception as e:
        log.error(f"Error constructing flight response: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing flight data: {e}")
        
    return response

@router.post("/bookFlight", response_model=schemas.FlightBookingResponse)
async def book_flight(
    data: schemas.FlightsRequest,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Searching flight: {data.departure} -> {data.arrival}")
    try:
        departure_codes = [c.strip().upper() for c in data.departure.split(",") if c.strip()]
        is_departure_iata = len(departure_codes) > 0 and all(len(c) == 3 and c in AIRPORTS_DB for c in departure_codes)

        if is_departure_iata:
            first_airport = AIRPORTS_DB[departure_codes[0]]
            stmt = select(models.VacationSession).filter(
                models.VacationSession.id == data.session_id,
                models.VacationSession.user_id == access_token.sub
            )
            result = await db.execute(stmt)
            session = result.scalars().first()
            currency = (session.currency if session else "EUR") or "EUR"
            results = {
                "departure_id": ",".join(departure_codes),
                "gl": first_airport.get('country', 'US').lower(),
                "hl": "en",
                "currency": currency
            }
        else:
            departure = data.departure.split(",")
            city = departure[0].strip()
            country = departure[1].strip() if len(departure) > 1 else None
            results = flights.get_location_data(city, country)

        arrival_codes = [c.strip().upper() for c in data.arrival.split(",") if c.strip()]
        is_arrival_iata = len(arrival_codes) > 0 and all(len(c) == 3 and c in AIRPORTS_DB for c in arrival_codes)

        if is_arrival_iata:
            arrival_id = ",".join(arrival_codes)
        else:
            arrival = data.arrival.split(",")
            city = arrival[0].strip()
            country = arrival[1].strip() if len(arrival) > 1 else None
            arrival_id = flights.get_location_data(city, country).get("departure_id")

        if not results.get("departure_id"):
             raise HTTPException(status_code=400, detail=f"Could not find airports for origin: {data.departure}")
        if not arrival_id:
            raise HTTPException(status_code=400, detail=f"Could not find airports for destination: {data.arrival}")
    except Exception as e:
        log.error(f"Error getting flight parameters: {e}")
        raise HTTPException(status_code=400, detail="Invalid location format")

    log.info("Searching for booking link...")
    booking_results = flights.call_flights_api(
        booking_token=data.token,
        departure_id=results.get("departure_id"),
        arrival_id=arrival_id,
        outbound_date=data.outbound_date,
        return_date=data.return_date,
        adults=data.adults,
        children=data.children,
        infants_in_seat=data.infants_in_seat,
        infants_on_lap=data.infants_on_lap,
        sort_by=data.sort_by,
        stops=data.stops,
        gl=results.get("gl"),
        hl=results.get("hl"),
        currency=results.get("currency")
    )
    url = booking_results.get("search_metadata", {}).get("google_flights_url")

    if not url:
        log.error("Booking failed: Incomplete booking information received.")
        raise HTTPException(status_code=500, detail="Booking failed")
    
    arrival_dt = None
    departure_dt = None
    
    try:
        if data.destination_arrival:
            arrival_dt = datetime.fromisoformat(data.destination_arrival.replace(" ", "T"))
        
        if data.destination_departure:
            departure_dt = datetime.fromisoformat(data.destination_departure.replace(" ", "T"))
    except ValueError as e:
        log.error(f"Error parsing flight times: {e}")
    
    try:
        stmt = (
            update(models.VacationSession)
            .where(
                models.VacationSession.id == data.session_id,
                models.VacationSession.user_id == access_token.sub
            )
            .values(
                flights_url=url,
                flight_price=data.price,
                flight_ccy=results.get("currency"),
                destination_arrival=arrival_dt,
                destination_departure=departure_dt,
            )
        )
        await db.execute(stmt)
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        log.error(f"Error updating session with flight booking URL: {e}")

    return schemas.FlightBookingResponse(
        booking_url=url
    )

@router.post("/getAccomodations", response_model=list[schemas.AccomodationsResponse])
async def get_accomodations(
    data: schemas.AccomodationsRequest,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Searching accomodations in {data.location}")
    try:
        destination = accomodations_v2.get_destination_id(
            location_name=data.location
        )
    except Exception as e:
        log.error(f"Error searching accomodations: {e}")
        raise HTTPException(status_code=500, detail="Error searching accomodations")

    if not destination or "dest_id" not in destination or "search_type" not in destination:
        log.warning("No accomodations found for the given criteria.")
        raise HTTPException(status_code=404, detail="No accomodations found")
    
    stmt = select(models.VacationSession).filter(
        models.VacationSession.id == data.session_id,
        models.VacationSession.user_id == access_token.sub
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    
    currency_code = session.currency if session and session.currency else "EUR"
    
    try:
        results = accomodations_v2.search_hotels(
            dest_id=destination.get("dest_id"),
            search_type=destination.get("search_type"),
            arrival_date=data.arrival_date,
            departure_date=data.departure_date,
            currency_code=currency_code,
            adults=data.adults,
            children=data.children,
            room_qty=data.room_qty,
            price_min=data.price_min,
            price_max=data.price_max,
        )

        if not results or results.get("message").lower() != "success":
            log.warning("No accomodations found for the given criteria.")
            raise HTTPException(status_code=404, detail="No accomodations found")
    except Exception as e:
        log.error(f"Error searching accomodations: {e}")
        raise HTTPException(status_code=500, detail="Error searching accomodations")
    
    hotels_list = results.get("data", {}).get("hotels")

    #sort hotels by price and return the first 5
    sorted_hotels = sorted(hotels_list, key=lambda x: x.get("property", {}).get("priceBreakdown", {}).get("grossPrice", {}).get("value", float('inf')))[:12]

    response = []
    for hotel in sorted_hotels:
        hotel_info = hotel.get("property", {})
        price_info = round(hotel_info.get("priceBreakdown", {}).get("grossPrice", {}).get("value", float('inf')), 2)
        ccy = hotel_info.get("priceBreakdown", {}).get("grossPrice", {}).get("currency")
        response.append(schemas.AccomodationsResponse(
            hotel_id=str(hotel.get("hotel_id", "")),
            hotel_name=hotel_info.get("name", ""),
            latitude=hotel_info.get("latitude"),
            longitude=hotel_info.get("longitude"),
            price=price_info,
            currency=ccy,
            photo_urls=hotel_info.get("photoUrls", []),
            accessibilityLabel=hotel.get("accessibilityLabel"),
            reviewScoreWord=hotel_info.get("reviewScoreWord"),
            reviewScore=hotel_info.get("reviewScore"),
            reviewCount=hotel_info.get("reviewCount"),
            propertyClass=hotel_info.get("propertyClass"),
            checkin_time_range=hotel_info.get("checkin", {}).get("fromTime") + ' - ' + hotel_info.get("checkin", {}).get("untilTime") if hotel_info.get("checkin") else None,
            checkout_time_range=hotel_info.get("checkout", {}).get("fromTime") + ' - ' + hotel_info.get("checkout", {}).get("untilTime") if hotel_info.get("checkout") else None,
        ))

    return response

@router.post("/getHotelDetails", response_model=schemas.HotelDetailsResponse)
async def get_hotel_details(
    data: schemas.AccomodationsRequest,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
):
    stmt = select(models.VacationSession).filter(
        models.VacationSession.id == data.session_id,
        models.VacationSession.user_id == access_token.sub
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    currency_code = session.currency if session and session.currency else "EUR"

    try:
        results = accomodations_v2.get_hotel_details(
            hotel_id=data.loc_id,
            arrival_date=data.arrival_date,
            departure_date=data.departure_date,
            currency_code=currency_code,
            adults=data.adults,
            children=data.children,
            room_qty=data.room_qty,
        )

        if not results or results.get("status") is False:
            raise HTTPException(status_code=404, detail="Hotel details not found")
            
        raw_data = results.get("data", {})

        room_info = next(iter(raw_data.get("rooms", {}).values()), None)
        description = raw_data.get("hotel_text", {}).get("description") or raw_data.get("description", "")
        if not description and room_info:
            description = room_info.get("description", "")
        
        facilities_data = raw_data.get("facilities_block", {})
        facilities_list = facilities_data.get("facilities", []) if isinstance(facilities_data, dict) else []
        amenities = [f.get("name") for f in facilities_list]

        photo_urls = [p.get("url_max1280") for p in room_info.get("photos", []) if p.get("url_max1280")]
        log.info(f"Extracted {len(photo_urls)} photo URLs for hotel {data.loc_id}")

        highlights = []
        for h in raw_data.get("property_highlight_strip", []):
            icons = h.get("icon_list", [])
            icon_val = icons[0].get("icon") if icons else None
            highlights.append({"name": h.get("name"), "icon": icon_val})

        blocks = raw_data.get("block", [])
        policies = blocks[0].get("block_text", {}).get("policies", []) if blocks else []
        cancel_p = next((p.get("content") for p in policies if p.get("class") == "POLICY_CANCELLATION"), None)
        prepay_p = next((p.get("content") for p in policies if p.get("class") == "POLICY_PREPAY"), None)

        rooms_data = raw_data.get("rooms", {})
        bed_info = "Bed information not available"
        if rooms_data and isinstance(rooms_data, dict):
            first_room = list(rooms_data.values())[0]
            bed_configs = first_room.get("bed_configurations", [])
            if bed_configs:
                bed_types = bed_configs[0].get("bed_types", [])
                bed_info = ", ".join([bt.get("name_with_count") for bt in bed_types])

        base_url = raw_data.get("url", "")
        deep_link_url = base_url

        if base_url:
            url_parts = list(urlparse(base_url))
            
            query = parse_qs(url_parts[4])
            
            query['checkin'] = [data.arrival_date]
            query['checkout'] = [data.departure_date]
            query['group_adults'] = [data.adults]
            query['req_adults'] = [data.adults]
            query['no_rooms'] = [data.room_qty]
            
            if data.children:
                child_list = [age.strip() for age in data.children.split(',')]
                
                query['group_children'] = [len(child_list)]
                query['req_children'] = [len(child_list)]
                
                query['age'] = child_list
                query['req_age'] = child_list
            else:
                query['group_children'] = [0]
                query['req_children'] = [0]
                
            url_parts[4] = urlencode(query, doseq=True)
            deep_link_url = urlunparse(url_parts)

        response = schemas.HotelDetailsResponse(
            hotel_id=str(raw_data.get("hotel_id")),
            url=deep_link_url,
            description=description,
            photos=photo_urls,
            amenities=amenities,
            sustainability_info=raw_data.get("sustainability"),
            property_highlights=highlights,
            languages_spoken=raw_data.get("spoken_languages", []),
            price_breakdown_details=raw_data.get("product_price_breakdown"),
            cancellation_policy=cancel_p,
            prepayment_policy=prepay_p,
            bed_details=bed_info,
            address=raw_data.get("address", "Exact address not available") + (f", {raw_data.get('district', '')}" if raw_data.get("district") else "")
        )
        
        return response
    
    except Exception as e:
        log.error(f"Error constructing hotel details: {e}")
        log.info(f"Raw response data: {results}")
        raise HTTPException(status_code=500, detail="Internal server error fetching details")

@router.post("/bookAccomodation", response_model=schemas.AccomodationBookingResponse)
async def book_accomodation(
    data: schemas.AccomodationBookingRequest,
    db: AsyncSession = Depends(get_db),
    access_token: TokenPayload = Depends(access_token_header)
    ):
    log.info(f"Saving booking URL for session {data.session_id}")
    
    try:
        stmt = (
            update(models.VacationSession)
            .where(
                models.VacationSession.id == data.session_id,
                models.VacationSession.user_id == access_token.sub
            )
            .values(
                accomodation_url=data.booking_url,
                accomodation_price=data.price,
                accomodation_ccy=data.currency
            )
        )
        
        result = await db.execute(stmt)
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")
            
        await db.commit()
        log.info(f"Successfully updated session {data.session_id} with booking URL.")
        
    except Exception as e:
        await db.rollback()
        log.error(f"Error updating session with accomodation booking URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error updating booking")

    return schemas.AccomodationBookingResponse(
        message="ok",
        booking_url=data.booking_url
    )

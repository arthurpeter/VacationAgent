from app.services.search import flights, accomodations_v2, explore
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.orm import Session
from authx import TokenPayload
from app.core.auth import auth
from datetime import datetime


log = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])

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
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Searching flights: {data.departure} -> {data.arrival}")
    try:
        departure = data.departure.split(",")
        city = departure[0].strip()
        country = departure[1].strip() if len(departure) > 1 else None
        log.info(f"Parsed departure: city='{city}', country='{country}'")
        results = flights.get_location_data(city, country)

        arrival = data.arrival.split(",")
        city = arrival[0].strip()
        country = arrival[1].strip() if len(arrival) > 1 else None
        log.info(f"Parsed arrival: city='{city}', country='{country}'")
        arrival_id = flights.get_location_data(city, country).get("departure_id")

        if not results.get("departure_id"):
             raise HTTPException(status_code=400, detail=f"Could not find airports for origin: {data.departure}")
        
        if not arrival_id:
             raise HTTPException(status_code=400, detail=f"Could not find airports for destination: {data.arrival}. Please try a specific city name.")

    except Exception as e:
        log.error(f"Error getting flight parameters: {e}")

    # UPDATE session currency preference, DATES, DESTINATION
    try:
        fmt = "%Y-%m-%d"
        dt_outbound = datetime.strptime(data.outbound_date, fmt)
        dt_return = datetime.strptime(data.return_date, fmt) if data.return_date else None
    except ValueError:
        log.error("Date format error")
        # Handle error or keep as None
        dt_outbound = None
        dt_return = None

    try:
        db.query(models.VacationSession).filter(
            models.VacationSession.id == data.session_id,
            models.VacationSession.user_id == access_token.sub
        ).update(
            {
            "currency": results.get("currency"),
            "from_date": dt_outbound,
            "to_date": dt_return,
            "departure": data.departure,
            "destination": data.arrival
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        log.error(f"Error updating session currency: {e}")

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
        for flight in all_flights[:5]:
            log.info(f"Flight: Price {flight.get('price')}")
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
                    departure=detail.get('departure_airport').get('name'),
                    departure_time=detail.get('departure_airport').get('time'),
                    arrival=detail.get('arrival_airport').get('name'),
                    arrival_time=detail.get('arrival_airport').get('time'),
                    duration=str(detail.get('duration', '')),
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
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Searching flight: {data.departure_id} -> {data.arrival_id}")
    try:
        departure = data.departure.split(",")
        city = departure[0].strip()
        country = departure[1].strip() if len(departure) > 1 else None
        results = flights.get_location_data(city, country)

        arrival = data.arrival.split(",")
        city = arrival[0].strip()
        country = arrival[1].strip() if len(arrival) > 1 else None
        arrival_id = flights.get_location_data(city, country).get("departure_id")
    except Exception as e:
        log.error(f"Error getting flight parameters: {e}")

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
        for flight in all_flights[:5]:
            log.info(f"Flight: Price {flight.price}")
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
                    departure=detail.get('departure_airport').get('name'),
                    departure_time=detail.get('departure_airport').get('time'),
                    arrival=detail.get('arrival_airport').get('name'),
                    arrival_time=detail.get('arrival_airport').get('time'),
                    duration=str(detail.get('duration', '')),
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
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Searching flight: {data.departure_id} -> {data.arrival_id}")
    try:
        departure = data.departure.split(",")
        city = departure[0].strip()
        country = departure[1].strip() if len(departure) > 1 else None
        results = flights.get_location_data(city, country)

        arrival = data.arrival.split(",")
        city = arrival[0].strip()
        country = arrival[1].strip() if len(arrival) > 1 else None
        arrival_id = flights.get_location_data(city, country).get("departure_id")
    except Exception as e:
        log.error(f"Error getting flight parameters: {e}")

    log.info("Searching for inbound flights...")
    booking_results = flights.call_flights_api(
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
        currency=results.get("currency")
    )
    url = booking_results.get("search_metadata", {}).get("google_flights_url")

    if not url:
        log.error("Booking failed: Incomplete booking information received.")
        raise HTTPException(status_code=500, detail="Booking failed")
    
    try:
        db.query(models.VacationSession).filter(
            models.VacationSession.id == data.session_id,
            models.VacationSession.user_id == access_token.sub
        ).update(
            {"flights_url": url}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        log.error(f"Error updating session with flight booking URL: {e}")

    return schemas.FlightBookingResponse(
        booking_url=url
    )

@router.post("/getAccomodations", response_model=list[schemas.AccomodationsResponse])
async def get_accomodations(
    data: schemas.AccomodationsRequest,
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
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
    
    currency_code = db.query(models.VacationSession).filter(
        models.VacationSession.id == data.session_id,
        models.VacationSession.user_id == access_token.sub
    ).first().currency or "EUR"
    
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
    sorted_hotels = sorted(hotels_list, key=lambda x: x.get("property", {}).get("priceBreakdown", {}).get("grossPrice", {}).get("value", float('inf')))[:5]

    response = []
    for hotel in sorted_hotels:
        hotel_info = hotel.get("property", {})
        price_info = hotel_info.get("priceBreakdown", {}).get("grossPrice", {}).get("value", float('inf'))
        response.append(schemas.AccomodationsResponse(
            hotel_id=str(hotel.get("hotel_id", "")),
            hotel_name=hotel_info.get("name", ""),
            latitude=hotel_info.get("latitude"),
            longitude=hotel_info.get("longitude"),
            price=price_info,
            currency=currency_code,
            photo_urls=hotel_info.get("photoUrls", []),
            accessibilityLabel=hotel.get("accessibilityLabel"),
            checkin_time_range=hotel_info.get("checkin", {}).get("fromTime") + ' - ' + hotel_info.get("checkin", {}).get("untilTime") if hotel_info.get("checkin") else None,
            checkout_time_range=hotel_info.get("checkout", {}).get("fromTime") + ' - ' + hotel_info.get("checkout", {}).get("untilTime") if hotel_info.get("checkout") else None,
        ))

    return response

@router.post("/bookAccomodation", response_model=schemas.AccomodationBookingResponse)
async def book_accomodation(
    data: schemas.AccomodationsRequest,
    db: Session = Depends(get_db),
    access_token: TokenPayload = Depends(auth.access_token_required)
    ):
    log.info(f"Request data: {data}")
    log.info(f"Booking accomodation: {data.hotel_id} in {data.location}")
    
    currency_code = db.query(models.VacationSession).filter(
        models.VacationSession.id == data.session_id,
        models.VacationSession.user_id == access_token.sub
    ).first().currency or "EUR"

    try:
        results = accomodations_v2.get_hotel_details(
            hotel_id=data.get("loc_id"),
            search_type=data.get("search_type"),
            arrival_date=data.arrival_date,
            departure_date=data.departure_date,
            currency_code=currency_code,
            adults=data.adults,
            children=data.children,
            room_qty=data.room_qty,
        )

        if not results or results.get("message").lower() != "success":
            log.warning("No accomodations found for the given criteria.")
            raise HTTPException(status_code=404, detail="No accomodations found")
    except Exception as e:
        log.error(f"Error searching accomodations: {e}")
        raise HTTPException(status_code=500, detail="Error searching accomodations")
    
    booking_url = results.get("data", {}).get("url")

    if not booking_url:
        log.error("Booking failed: Incomplete booking information received.")
        raise HTTPException(status_code=500, detail="Booking failed")
    
    try:
        db.query(models.VacationSession).filter(
            models.VacationSession.id == data.session_id,
            models.VacationSession.user_id == access_token.sub
        ).update(
            {"accomodation_url": booking_url}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        log.error(f"Error updating session with accomodation booking URL: {e}")

    return schemas.AccomodationBookingResponse(
        booking_url=booking_url
    )
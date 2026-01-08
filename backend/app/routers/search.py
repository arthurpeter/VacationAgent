from app.services.search import flights, accomodations_v2, explore
from fastapi import APIRouter, Depends, HTTPException
from app import schemas
from app.core.logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("/exploreDestinations", response_model=list[schemas.ExploreDestination])
async def explore_destinations(data: schemas.ExploreRequest):
    pass

@router.post("/getOutboundFlights", response_model=list[schemas.FlightsResponse])
async def search_outbound_flights(data: schemas.FlightsRequest):
    log.info(f"Searching flights: {data.departure} -> {data.arrival}")
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

    log.info("Searching for outbound flights...")
    flight_results = flights.search_flights(
        departure_id=results.get("departure_id"),
        arrival_id=arrival_id,
        outbound_date=data.outbound_date,
        return_date=data.return_date,
        adults=data.adults,
        children=data.children,
        infants_in_seat=data.infants_in_seat,
        infants_in_lap=data.infants_in_lap,
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
            log.info(f"Flight: Price {flight.price}")
            flight_schema = schemas.FlightsResponse(
                token=flight.get('departure_token'),
                price=flight.get('price'),
                flights=[]
            )
            for detail in flight.get('flights', []):
                flight_detail = schemas.Flight(
                    airline=detail.get('airline', ''),
                    departure=detail.get('departure_airport').get('name'),
                    departure_time=detail.get('departure_airport').get('time'),
                    arrival=detail.get('arrival_airport').get('name'),
                    arrival_time=detail.get('arrival_airport').get('time'),
                    duration=detail.get('duration', ''),
                )
                flight_schema.flights.append(flight_detail)
            response.append(flight_schema)
    except Exception as e:
        log.error(f"Error constructing flight response: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing flight data: {e}")
        
    return response

@router.post("/getInboundFlights", response_model=list[schemas.FlightsResponse])
async def search_inbound_flights(data: schemas.FlightsRequest):
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
    flight_results = flights.search_flights(
        departure_token=data.token,
        departure_id=results.get("departure_id"),
        arrival_id=arrival_id,
        outbound_date=data.outbound_date,
        return_date=data.return_date,
        adults=data.adults,
        children=data.children,
        infants_in_seat=data.infants_in_seat,
        infants_in_lap=data.infants_in_lap,
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
            log.info(f"Flight: Price {flight.price}")
            flight_schema = schemas.FlightsResponse(
                token=flight.get('booking_token'),
                price=flight.get('price'),
                flights=[]
            )
            for detail in flight.get('flights', []):
                flight_detail = schemas.Flight(
                    airline=detail.get('airline', ''),
                    departure=detail.get('departure_airport').get('name'),
                    departure_time=detail.get('departure_airport').get('time'),
                    arrival=detail.get('arrival_airport').get('name'),
                    arrival_time=detail.get('arrival_airport').get('time'),
                    duration=detail.get('duration', ''),
                )
                flight_schema.flights.append(flight_detail)
            response.append(flight_schema)
    except Exception as e:
        log.error(f"Error constructing flight response: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing flight data: {e}")
        
    return response

@router.post("/BookFlight", response_model=schemas.FlightBookingResponse)
async def book_flight(data: schemas.FlightsRequest):
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
    booking_results = flights.search_flights(
        departure_token=data.token,
        departure_id=results.get("departure_id"),
        arrival_id=arrival_id,
        outbound_date=data.outbound_date,
        return_date=data.return_date,
        adults=data.adults,
        children=data.children,
        infants_in_seat=data.infants_in_seat,
        infants_in_lap=data.infants_in_lap,
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

    return schemas.FlightBookingResponse(
        booking_url=url
    )
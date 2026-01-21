"""Schemas for vacation-related data."""

from typing import Optional
from pydantic import BaseModel

class Flight(BaseModel):
    """Schema for individual flight details."""
    airline: str
    departure: str
    departure_time: str
    arrival: str
    arrival_time: str
    duration: str

class FlightsResponse(BaseModel):
    """Schema for flight search response."""
    token: str
    price: float
    flights: list[Flight]

class FlightBookingResponse(BaseModel):
    """Schema for flight booking response."""
    booking_url: str

class FlightsRequest(BaseModel):
    """Schema for flight search request."""
    session_id: str
    token: Optional[str] = None
    departure: str
    arrival: str
    outbound_date: str
    return_date: Optional[str] = None
    adults: int
    children: Optional[int] = 0
    infants_in_seat: Optional[int] = 0
    infants_on_lap: Optional[int] = 0
    sort_by: Optional[int] = 2
    stops: Optional[int] = 0

class ExploreResponse(BaseModel):
    """Schema for explore flight search response."""
    start_date: str
    end_date: str

class ExploreRequest(BaseModel):
    """Schema for explore flight search request."""
    departure: str
    arrival: str
    duration_type: int
    month: int
    adults: int
    children: Optional[int] = 0
    infants_in_seat: Optional[int] = 0
    infants_on_lap: Optional[int] = 0
    stops: Optional[int] = 0

class AccomodationsRequest(BaseModel):
    """Schema for accomodations search request."""
    session_id: str
    loc_id: Optional[str]
    location: str
    search_type: str # e.g., "CITY"
    arrival_date: str
    departure_date: str
    adults: Optional[int]
    children: Optional[str]
    room_qty: Optional[int]
    price_min: Optional[int]
    price_max: Optional[int]

class AccomodationsResponse(BaseModel):
    """Schema for accomodations search response."""
    hotel_id: str
    hotel_name: str
    address: str
    price: float
    currency: str
    photo_urls: list[str]
    accessibilityLabel: Optional[str]
    checkin_time_range: Optional[str]
    checkout_time_range: Optional[str]

class AccomodationBookingResponse(BaseModel):
    """Schema for accomodation booking response."""
    booking_url: str

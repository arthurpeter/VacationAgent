# Search Services Documentation
This directory contains the logic for interacting with external travel APIs. The services allow the Vacation Agent to fetch real-time data for flights, accommodations, and destination inspiration.

Table of Contents
Configuration

Flights Service

Accommodations Service v2

Explore Service

## Configuration
Before using these services, ensure the following keys are present in your .env file:

### Required for Flights, Accommodations v1, and Explore
SERPAPI_API_KEY=your_serpapi_key_here

### Required for Accommodations v2 (Booking.com)
RAPIDAPI_KEY=your_rapidapi_key_here


## Flights Service (Google Flights via SerpApi)
Source: flights.py
Provider: SerpApi Google Flights Engine

This service executes a multi-step search to find round-trip flights. Unlike simple search APIs, Google Flights requires a "token" exchange flow to reach the final booking link.

Workflow
Outbound Search: Searches for flights from Origin A to Destination B. Returns a departure_token.

Return Search: Uses the departure_token to find return flights. Returns a booking_token.

Booking Link Retrieval: Uses the booking_token to retrieve the final URL for the specific itinerary.

Docs: https://serpapi.com/google-flights-api

## Accommodations Service v2 (Booking.com via RapidAPI)
Source: accomodations_v2.py
Provider: Booking.com API via RapidAPI

This is an alternative accommodation service that queries Booking.com directly. It follows a strictly hierarchical flow: find the location ID first, then search for hotels, then fetch details for deep links.

Workflow
Destination Search: (get_destination_id) Maps a string (e.g., "Paris") to a dest_id and search_type.

Hotel Search: (Google Hotels) Uses the dest_id to retrieve a list of hotels and prices.

Hotel Details: (get_hotel_details) Uses hotel_id to fetch the specific hotelUrl (Deep link).

Docs: https://rapidapi.com/apiheya/api/booking-com15/playground/apiendpoint_818c2744-8507-4071-829e-d080b667a06c (destination id)
      https://rapidapi.com/apiheya/api/booking-com15/playground/apiendpoint_361975f8-6740-4efa-a2ad-1815f4b7d4ac (hotel offerings)
      https://rapidapi.com/apiheya/api/booking-com15/playground/apiendpoint_e52b8669-a586-4c8a-be83-52aaa75f99bc (booking link)

## Explore Service (Google Travel Explore via SerpApi)
Source: explore.py
Provider: SerpApi Google Travel Explore

This service is used for "Inspiration" queries. It allows open-ended searches such as "Flights from New York to Europe in September" without requiring a specific city or exact dates. It returns general pricing for various destinations on a map view.

Key Features
Supports broad region searches (e.g., "Europe").

Supports flexible dates (e.g., specific month or "6 months").

Returns destination images and approximate flight costs.

Docs: https://serpapi.com/google-travel-explore-api
import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
// import { fetchWithAuth } from '../../authService'; // Uncomment when ready

export default function OptionsStage() {
  const { sessionData, refreshContext } = useOutletContext();
  const [loading, setLoading] = useState(false);
  
  // --- 1. Local State for Filters (Editable) ---
  // We initialize these from the session/DB, but allow manual edits
  const memory = sessionData?.data || {};
  
  const [filters, setFilters] = useState({
    destination: "",
    startDate: "",
    endDate: "",
    adults: 1,
    budget: ""
  });

  // Sync with DB data when it loads (only if user hasn't typed yet or on first load)
  useEffect(() => {
    if (sessionData?.data) {
      setFilters(prev => ({
        destination: prev.destination || sessionData.data.destination || "",
        startDate: prev.startDate || sessionData.data.departure_date || "",
        endDate: prev.endDate || sessionData.data.return_date || "",
        adults: prev.adults || sessionData.data.adults || 1,
        budget: prev.budget || sessionData.data.budget || ""
      }));
    }
  }, [sessionData]);

  // Local state for search results
  const [flights, setFlights] = useState([]);
  const [hotels, setHotels] = useState([]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSearch = async () => {
    setLoading(true);
    console.log("Searching with manual/AI filters:", filters);

    // TODO: Call your backend Search API here using 'filters' object
    // await fetchWithAuth(`http://localhost:5000/vacations/${id}/search`, { body: filters }, "POST");

    // Mock Response Delay
    setTimeout(() => {
      setFlights(MOCK_FLIGHTS);
      setHotels(MOCK_HOTELS);
      setLoading(false);
      // In real implementation: refreshContext() to save these new manual inputs to the DB
    }, 1500);
  };

  return (
    <div className="flex flex-col w-full h-full bg-gray-50 overflow-hidden">
      {/* --- Editable Control Bar --- */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm shrink-0 flex flex-wrap gap-4 items-end">
        
        {/* Destination Input */}
        <div className="flex flex-col gap-1 w-48">
            <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Destination</label>
            <input 
                name="destination"
                value={filters.destination}
                onChange={handleInputChange}
                placeholder="Where to?"
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-bold text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
        </div>

        {/* Dates Inputs */}
        <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Dates</label>
            <div className="flex items-center gap-2">
                <input 
                    name="startDate"
                    type="date"
                    value={filters.startDate}
                    onChange={handleInputChange}
                    className="border border-gray-300 rounded-lg px-2 py-2 text-sm text-gray-700 focus:ring-blue-500"
                />
                <span className="text-gray-400">-</span>
                <input 
                    name="endDate"
                    type="date"
                    value={filters.endDate}
                    onChange={handleInputChange}
                    className="border border-gray-300 rounded-lg px-2 py-2 text-sm text-gray-700 focus:ring-blue-500"
                />
            </div>
        </div>

        {/* Travelers & Budget */}
        <div className="flex flex-col gap-1 w-24">
             <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Adults</label>
             <input 
                name="adults"
                type="number"
                min="1"
                value={filters.adults}
                onChange={handleInputChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-bold text-gray-800"
            />
        </div>

        <div className="flex flex-col gap-1 w-32">
             <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Budget ($)</label>
             <input 
                name="budget"
                type="number"
                placeholder="2000"
                value={filters.budget}
                onChange={handleInputChange}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-bold text-gray-800"
            />
        </div>
        
        <div className="flex-grow"></div>
        
        {/* Search Button */}
        <button 
          onClick={handleSearch}
          disabled={loading || !filters.destination}
          className={`h-10 px-6 rounded-lg font-semibold text-white transition shadow-md ${
            loading || !filters.destination 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? "Searching..." : "Find Options"}
        </button>
      </div>

      {/* Results Area */}
      <div className="flex-grow overflow-y-auto p-8">
        <div className="max-w-6xl mx-auto space-y-10">
          
          {/* Flights Section */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              ✈️ Flights
            </h2>
            {flights.length === 0 ? (
               <EmptyState text="Enter a destination and dates above to find flights." />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {flights.map((flight) => (
                  <FlightCard key={flight.id} flight={flight} />
                ))}
              </div>
            )}
          </section>

          {/* Hotels Section */}
          <section>
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              🏨 Accommodations
            </h2>
             {hotels.length === 0 ? (
               <EmptyState text="We'll find hotels that match your budget." />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {hotels.map((hotel) => (
                  <HotelCard key={hotel.id} hotel={hotel} />
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

// --- Sub-components (Same as before) ---

function EmptyState({ text }) {
    return (
        <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center text-gray-400 bg-gray-50/50">
            {text}
        </div>
    )
}

function FlightCard({ flight }) {
  return (
    <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition">
      <div className="flex justify-between items-start mb-4">
        <div className="font-bold text-lg text-gray-800">{flight.airline}</div>
        <div className="text-blue-600 font-bold text-xl">${flight.price}</div>
      </div>
      <div className="flex justify-between items-center text-sm text-gray-600 mb-4">
        <div>
            <div className="font-semibold">{flight.departure_time}</div>
            <div className="text-gray-400">{flight.origin}</div>
        </div>
        <div className="text-xs text-gray-300">────────✈────────</div>
        <div className="text-right">
            <div className="font-semibold">{flight.arrival_time}</div>
            <div className="text-gray-400">{flight.destination}</div>
        </div>
      </div>
      <button className="w-full py-2 rounded-lg border border-blue-100 text-blue-600 hover:bg-blue-50 font-semibold text-sm transition">
        Select Offer
      </button>
    </div>
  );
}

function HotelCard({ hotel }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition overflow-hidden flex flex-col h-full">
      <div className="h-40 bg-gray-200 relative">
        <div className="absolute top-2 right-2 bg-white/90 px-2 py-1 rounded text-xs font-bold shadow-sm">
            ⭐ {hotel.rating}
        </div>
      </div>
      <div className="p-4 flex flex-col flex-grow">
        <h3 className="font-bold text-gray-800 mb-1 line-clamp-1">{hotel.name}</h3>
        <p className="text-xs text-gray-500 mb-3 line-clamp-2">{hotel.description}</p>
        <div className="mt-auto flex justify-between items-end">
            <span className="text-sm text-gray-400">per night</span>
            <span className="text-lg font-bold text-gray-900">${hotel.price}</span>
        </div>
      </div>
    </div>
  );
}

// --- Mock Data ---
const MOCK_FLIGHTS = [
    { id: 1, airline: "Lufthansa", price: 450, origin: "OTP", destination: "CDG", departure_time: "06:00", arrival_time: "08:30" },
    { id: 2, airline: "Air France", price: 520, origin: "OTP", destination: "CDG", departure_time: "14:00", arrival_time: "16:40" },
];

const MOCK_HOTELS = [
    { id: 1, name: "Hotel Le A", rating: 4.8, price: 220, description: "Boutique hotel near Champs-Elysées with modern art decor." },
    { id: 2, name: "Grand Hotel", rating: 4.5, price: 180, description: "Classic luxury in the heart of the city." },
    { id: 3, name: "City Flat", rating: 4.2, price: 120, description: "Cozy apartment perfect for couples." },
];
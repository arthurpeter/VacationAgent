import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { toast, Toaster } from 'react-hot-toast';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import PageTransition from '../../components/PageTransition';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

function useDebounce(value, delay) {
    const [debouncedValue, setDebouncedValue] = useState(value);
    useEffect(() => {
        const handler = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);
        return () => {
            clearTimeout(handler);
        };
    }, [value, delay]);
    return debouncedValue;
}

function LocationAutocomplete({ label, value, onChange, placeholder }) {
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    
    const wrapperRef = useRef(null);
    const cache = useRef({});
    const isSelectionEvent = useRef(false);
    
    const debouncedValue = useDebounce(value, 300);

    useEffect(() => {
        const controller = new AbortController();

        const fetchSuggestions = async () => {
            const query = debouncedValue?.trim();
            
            if (isSelectionEvent.current) {
                isSelectionEvent.current = false;
                return;
            }

            if (!query) {
                setSuggestions([]);
                setShowSuggestions(false);
                return;
            }

            if (cache.current[query]) {
                setSuggestions(cache.current[query]);
                setShowSuggestions(true);
                return;
            }

            setIsLoading(true);
            
            try {
                const res = await fetch(
                    `https://nominatim.openstreetmap.org/search?format=json&q=${query}&addressdetails=1&limit=5&accept-language=en`,
                    { signal: controller.signal }
                );
                
                if (res.ok) {
                    const data = await res.json();
                    cache.current[query] = data;
                    setSuggestions(data);
                    setShowSuggestions(true);
                }
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error("Autocomplete fetch error", err);
                }
            } finally {
                setIsLoading(false);
            }
        };

        fetchSuggestions();

        return () => controller.abort();
    }, [debouncedValue]);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const handleInput = (e) => {
        isSelectionEvent.current = false; 
        onChange(e.target.value, false);
    };

    const selectSuggestion = (item) => {
        const city = item.address.city || item.address.town || item.address.village || item.name;
        const country = item.address.country_code ? item.address.country_code.toUpperCase() : "";
        const formatted = city && country ? `${city}, ${country}` : item.display_name;
        
        isSelectionEvent.current = true;
        
        onChange(formatted, true);
        setShowSuggestions(false);
    };

    return (
        <div className="flex flex-col gap-1 w-48 relative" ref={wrapperRef}>
            <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">{label}</label>
            <div className="relative">
                <input 
                    value={value}
                    onChange={handleInput}
                    placeholder={placeholder}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-bold text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full pr-8"
                />
                
                {isLoading && (
                    <div className="absolute right-2 top-2.5">
                        <svg className="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    </div>
                )}
            </div>

            {showSuggestions && suggestions.length > 0 && (
                <ul className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-xl mt-1 z-50 max-h-60 overflow-y-auto">
                    {suggestions.map((item, idx) => (
                        <li 
                            key={idx} 
                            onClick={() => selectSuggestion(item)}
                            className="px-4 py-2 hover:bg-blue-50 cursor-pointer text-sm text-gray-700 truncate border-b border-gray-50 last:border-0"
                        >
                            <span className="font-bold text-gray-800">{item.address.city || item.name}</span>
                            <span className="text-gray-400 text-xs ml-2">{item.address.country}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

function TravelersInput({ counts, setCounts, childAges, setChildAges, onSave }) {
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef(null);

    const ageSaveTimer = useRef(null);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const totalTravelers = counts.adults + counts.children + counts.infantsSeat + counts.infantsLap;

    const updateCount = (type, delta) => {
        const currentVal = counts[type];
        const newVal = Math.max(0, currentVal + delta);
        
        if (type === 'adults' && newVal < 1) return;
        
        let newAges = [...childAges];

        if (type === 'children' || type === 'infantsSeat' || type === 'infantsLap') {
            const currentTotalKids = counts.children + counts.infantsSeat + counts.infantsLap;
            const newTotalKids = currentTotalKids + (newVal - currentVal);
            
            if (newTotalKids > currentTotalKids) {
                newAges = [...newAges, "5"];
            } else if (newTotalKids < currentTotalKids) {
                newAges = newAges.slice(0, -1);
            }
        }

        const newCounts = { ...counts, [type]: newVal };
        setCounts(newCounts);
        setChildAges(newAges);

        onSave({
            adults: newCounts.adults,
            children: newCounts.children,
            infants_in_seat: newCounts.infantsSeat,
            infants_on_lap: newCounts.infantsLap,
            children_ages: newAges.join(',')
        });
    };

    const updateAge = (index, val) => {
        const newAges = [...childAges];
        newAges[index] = val;
        setChildAges(newAges);
        
        if (ageSaveTimer.current) clearTimeout(ageSaveTimer.current);
        ageSaveTimer.current = setTimeout(() => {
            onSave({ children_ages: newAges.join(',') });
        }, 500);
    };

    return (
        <div className="flex flex-col gap-1 w-40 relative" ref={wrapperRef}>
            <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Travelers</label>
            <button 
                onClick={() => setIsOpen(!isOpen)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-bold text-gray-800 text-left bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                {totalTravelers} Traveler{totalTravelers !== 1 ? 's' : ''}
            </button>
            
            {isOpen && (
                <div className="absolute top-full left-0 w-72 bg-white border border-gray-200 rounded-xl shadow-2xl mt-2 z-50 p-4">
                    <div className="space-y-4 mb-4">
                        {[
                            { id: 'adults', label: 'Adults', sub: 'Age 12+' },
                            { id: 'children', label: 'Children', sub: 'Age 2-11' },
                            { id: 'infantsSeat', label: 'Infants', sub: 'In seat' },
                            { id: 'infantsLap', label: 'Infants', sub: 'On lap' },
                        ].map((type) => (
                            <div key={type.id} className="flex justify-between items-center">
                                <div>
                                    <div className="font-bold text-gray-800 text-sm">{type.label}</div>
                                    <div className="text-xs text-gray-400">{type.sub}</div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <button onClick={() => updateCount(type.id, -1)} className="w-8 h-8 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200">-</button>
                                    <span className="w-4 text-center font-bold text-sm">{counts[type.id]}</span>
                                    <button onClick={() => updateCount(type.id, 1)} className="w-8 h-8 rounded-full bg-blue-50 text-blue-600 hover:bg-blue-100">+</button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {childAges.length > 0 && (
                        <div className="border-t border-gray-100 pt-3">
                            <div className="text-xs font-bold text-gray-500 mb-2">Child Ages (Required for Hotels)</div>
                            <div className="grid grid-cols-4 gap-2">
                                {childAges.map((age, i) => (
                                    <input 
                                        key={i}
                                        type="number"
                                        min="0"
                                        max="17"
                                        value={age}
                                        onChange={(e) => updateAge(i, e.target.value)}
                                        className="border border-gray-300 rounded p-1 text-center text-sm"
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function HotelDetailsModal({ hotel, details, isLoading, onClose, onSelect }) {
    if (!hotel) return null;

    const position = [hotel.latitude || 0, hotel.longitude || 0];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="bg-white w-full max-w-6xl h-[90vh] rounded-3xl shadow-2xl overflow-hidden flex flex-col relative animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-white z-10">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                            <h2 className="text-2xl font-black text-gray-900">{hotel.hotel_name}</h2>
                            <span className="text-orange-400 text-sm">{"⭐".repeat(hotel.propertyClass)}</span>

                            {hotel.reviewScore && (
                                <div className="flex items-center bg-blue-600 text-white rounded-md px-2 py-1 shadow-sm ml-2">
                                    <span className="font-bold text-lg leading-none">{hotel.reviewScore}</span>
                                    <div className="flex flex-col ml-2 leading-none border-l border-blue-500 pl-2">
                                        <span className="text-[10px] uppercase font-bold text-blue-100 tracking-wider">{hotel.reviewScoreWord}</span>
                                        <span className="text-[9px] text-blue-200">{hotel.reviewCount} reviews</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        <p className="text-gray-500 text-sm flex items-center gap-1">
                            <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg>
                            <span className="font-medium">{details?.address || hotel.location_string || "Address details loading..."}</span>
                        </p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition">
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto p-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">

                        <div className="lg:col-span-2 space-y-8">

                            <div className="grid grid-cols-4 grid-rows-2 gap-3 h-96">
                                <div className="col-span-2 row-span-2 rounded-2xl overflow-hidden bg-gray-100 relative">
                                    <img src={details?.photos?.[0] || hotel.photo_urls?.[0]} className="w-full h-full object-cover" alt="Main View" />
                                </div>
                                {(details?.photos?.slice(1, 5) || [null, null, null, null]).map((url, i) => (
                                    <div key={i} className="rounded-xl overflow-hidden bg-gray-100 relative">
                                        {url ? (
                                            <img src={url} className="w-full h-full object-cover" alt={`Gallery ${i}`} />
                                        ) : (
                                            <div className="animate-pulse w-full h-full bg-gray-200" />
                                        )}
                                    </div>
                                ))}
                            </div>

                            <div className="flex flex-wrap gap-4">
                                {details?.property_highlights?.map((h, i) => (
                                    <div key={i} className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-xs font-bold">
                                        <span>{h.name}</span>
                                    </div>
                                ))}
                            </div>

                            <div>
                                <h3 className="text-lg font-bold mb-3">About this property</h3>
                                {isLoading ? (
                                    <div className="space-y-2">
                                        <div className="h-4 bg-gray-100 rounded w-full animate-pulse"/>
                                        <div className="h-4 bg-gray-100 rounded w-5/6 animate-pulse"/>
                                    </div>
                                ) : (
                                    <p className="text-gray-600 leading-relaxed text-sm whitespace-pre-line">
                                        {details?.description || "No description available."}
                                    </p>
                                )}
                            </div>

                            {details?.languages_spoken?.length > 0 && (
                                <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
                                    <h3 className="text-sm font-bold text-gray-800 uppercase tracking-wide mb-3 flex items-center gap-2">
                                        <span className="text-lg">🗣️</span> Languages Spoken
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {details.languages_spoken.map((lang, i) => (
                                            <span key={i} className="px-3 py-1 bg-white text-gray-700 text-xs font-bold rounded-full border border-gray-200 uppercase shadow-sm">
                                                {lang}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div>
                                <h3 className="text-lg font-bold mb-3">Location</h3>
                                <div className="h-64 w-full bg-gray-100 rounded-2xl overflow-hidden border border-gray-200 relative z-0">
                                    <MapContainer 
                                        key={hotel.hotel_id} 
                                        center={position} 
                                        zoom={15} 
                                        scrollWheelZoom={false} 
                                        style={{ height: "100%", width: "100%" }}
                                    >
                                        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                                        <Marker position={position}>
                                            <Popup>
                                                <div className="font-bold">{hotel.hotel_name}</div>
                                            </Popup>
                                        </Marker>
                                    </MapContainer>
                                </div>
                            </div>

                        </div>

                        <div className="lg:col-span-1">
                            <div className="bg-gray-50 p-6 rounded-2xl border border-gray-200 sticky top-0 space-y-6">
                                <div>
                                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Pricing Breakdown</span>
                                    <div className="text-4xl font-black text-blue-700 mt-2">{hotel.price} {hotel.currency}</div>
                                    <p className="text-xs text-green-600 font-bold mt-1">
                                        {details?.price_breakdown_details?.composite_price_breakdown?.items?.[0]?.translated_copy || "Includes taxes & fees"}
                                    </p>
                                </div>

                                <div className="grid grid-cols-2 gap-3 py-4 border-t border-gray-200">
                                    <div className="bg-white p-2 rounded border border-gray-200 text-center">
                                        <div className="text-[9px] uppercase text-gray-400 font-bold mb-1">Check-in</div>
                                        <div className="text-sm font-bold text-gray-800">{hotel.checkin_time_range || "14:00+"}</div>
                                    </div>
                                    <div className="bg-white p-2 rounded border border-gray-200 text-center">
                                        <div className="text-[9px] uppercase text-gray-400 font-bold mb-1">Check-out</div>
                                        <div className="text-sm font-bold text-gray-800">{hotel.checkout_time_range || "11:00"}</div>
                                    </div>
                                </div>

                                <div className="space-y-3 pb-4 border-b border-gray-200">
                                    <div className="flex items-center gap-3 text-sm">
                                        <span className="text-lg">🛏️</span>
                                        <span className="font-bold text-gray-700">{details?.bed_details || "Standard Bedding"}</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-sm">
                                        <span className="text-lg">🛡️</span>
                                        <span className="text-gray-600">{details?.cancellation_policy || "Check cancellation terms"}</span>
                                    </div>
                                </div>

                                <button 
                                    disabled={isLoading}
                                    onClick={() => onSelect({ ...hotel, booking_url: details.url })}
                                    className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-xl shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? "Loading Details..." : "Select & Save this Hotel"}
                                </button>
                                
                                {details?.sustainability_info && (
                                    <div className="p-4 bg-green-50 rounded-xl border border-green-100">
                                        <div className="flex items-center gap-2 text-green-700 font-bold text-xs mb-1">
                                            <span>🌿</span> {details.sustainability_info.hotel_page.title}
                                        </div>
                                        <p className="text-[10px] text-green-600">{details.sustainability_info.hotel_page.description}</p>
                                    </div>
                                )}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
}

function FlightDetailsModal({ flight, onClose }) {
    if (!flight) return null;

    const segments = flight.flights;

    const formatDuration = (mins) => {
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        return `${h}h ${m}m`;
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="bg-white w-full max-w-3xl max-h-[90vh] rounded-3xl shadow-2xl overflow-hidden flex flex-col relative animate-in fade-in zoom-in duration-200">
                
                <div className="flex justify-between items-center p-6 border-b border-gray-100 bg-white z-10 shrink-0">
                    <div>
                        <h2 className="text-2xl font-black text-gray-900">Flight Details</h2>
                        <div className="text-blue-600 font-bold text-xl mt-1">{flight.price} {flight.currency}</div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition">
                        <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto p-6 bg-gray-50">
                    <div className="space-y-4">
                        {segments.map((leg, i) => {
                            let layoverStr = null;
                            let layoverCity = null;
                            if (i < segments.length - 1) {
                                const nextLeg = segments[i + 1];
                                const arrival = new Date(leg.arrival_time.replace(" ", "T"));
                                const departure = new Date(nextLeg.departure_time.replace(" ", "T"));
                                const diffMins = Math.floor((departure - arrival) / 60000);
                                if (diffMins > 0) {
                                    layoverStr = formatDuration(diffMins);
                                    layoverCity = leg.arrival.split(',')[0];
                                }
                            }

                            return (
                                <React.Fragment key={i}>
                                    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                                        <div className="flex items-center gap-3 mb-4 border-b border-gray-100 pb-3">
                                            {leg.airline_logo && <img src={leg.airline_logo} alt={leg.airline} className="h-6 w-6 object-contain" />}
                                            <span className="font-bold text-gray-800">{leg.airline}</span>
                                            
                                            {leg.airplane && (
                                                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-md">
                                                    {leg.airplane}
                                                </span>
                                            )}
                                            
                                            <span className="text-gray-400 text-sm ml-auto">Duration: {formatDuration(parseInt(leg.duration) || 0)}</span>
                                        </div>
                                        
                                        <div className="flex justify-between items-center">
                                            <div className="flex-1">
                                                <div className="text-2xl font-black text-gray-900">{leg.departure_time.split(" ")[1]}</div>
                                                <div className="text-sm font-bold text-gray-600">{leg.departure}</div>
                                                <div className="text-xs text-gray-400">{leg.departure_time.split(" ")[0]}</div>
                                            </div>
                                            
                                            <div className="px-4 text-gray-300">➔</div>
                                            
                                            <div className="flex-1 text-right">
                                                <div className="text-2xl font-black text-gray-900">{leg.arrival_time.split(" ")[1]}</div>
                                                <div className="text-sm font-bold text-gray-600">{leg.arrival}</div>
                                                <div className="text-xs text-gray-400">{leg.arrival_time.split(" ")[0]}</div>
                                            </div>
                                        </div>

                                        {leg.extensions && leg.extensions.length > 0 && (
                                            <div className="mt-4 pt-3 border-t border-gray-50 flex flex-wrap gap-2">
                                                {leg.extensions.map((ext, extIdx) => (
                                                    <span key={extIdx} className="text-[10px] bg-blue-50 text-blue-700 px-2 py-1 rounded font-medium">
                                                        {ext}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {layoverStr && (
                                        <div className="flex items-center justify-center -my-2 relative z-10">
                                            <div className="bg-orange-100 border border-orange-200 text-orange-800 text-xs font-bold px-4 py-1.5 rounded-full shadow-sm">
                                                Layover: {layoverStr} in {layoverCity}
                                            </div>
                                        </div>
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function OptionsStage() {
  const { sessionData, refreshContext } = useOutletContext();
  const session = sessionData?.data || sessionData;
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState('SEARCH'); 

  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [dates, setDates] = useState({ start: "", end: "" });
  
  const [travelerCounts, setTravelerCounts] = useState({
      adults: 1,
      children: 0,
      infantsSeat: 0,
      infantsLap: 0
  });
  const [childAges, setChildAges] = useState([]);
  const [roomQty, setRoomQty] = useState(1);
  const [booked, setBooked] = useState({ flights: false, hotel: false });

  const [viewingFlight, setViewingFlight] = useState(null); 
  const [maxStops, setMaxStops] = useState(0); 
  const [sortBy, setSortBy] = useState(2);

  const [viewingHotel, setViewingHotel] = useState(null); 
  const [selectedHotelDetails, setSelectedHotelDetails] = useState(null); 
  const [loadingDetails, setLoadingDetails] = useState(false); 
  
  const [outboundFlights, setOutboundFlights] = useState([]);
  const [inboundFlights, setInboundFlights] = useState([]);
  const [hotels, setHotels] = useState([]);
  
  const [selectedOutbound, setSelectedOutbound] = useState(null);
  const [selectedInbound, setSelectedInbound] = useState(null);
  const [selectedHotel, setSelectedHotel] = useState(null);

  const saveToSession = async (payload) => {
    if (!sessionData?.id) return;
    try {
        await fetchWithAuth(`${API_BASE_URL}/session/${sessionData.id}/details`, payload, 'PATCH');
        console.log("Auto-saved to session:", payload);

        if (refreshContext) {
            refreshContext();
        }
    } catch (err) {
        console.error("Failed to auto-save session data", err);
    }
  };

  useEffect(() => {
    if (!session) return;
    
    if (session.departure) setOrigin(session.departure);
    if (session.destination) setDestination(session.destination);
    
    const formatForInput = (isoString) => {
        if (!isoString) return "";
        return isoString.split("T")[0];
    };
    setDates({
        start: formatForInput(session.from_date),
        end: formatForInput(session.to_date)
    });

    if (session.adults !== undefined) {
        setTravelerCounts({
            adults: session.adults || 1,
            children: session.children || 0,
            infantsSeat: session.infants_in_seat || 0,
            infantsLap: session.infants_on_lap || 0
        });
    }
    
    if (session.children_ages) {
        setChildAges(session.children_ages.split(',').filter(age => age !== ''));
    }

    if (session.room_qty) {
        setRoomQty(session.room_qty);
    }
  }, [session]);

  useEffect(() => {
      if (roomQty > travelerCounts.adults) {
          setRoomQty(travelerCounts.adults);
      }
  }, [travelerCounts.adults, roomQty]);


  
  const handleLocationChange = (type, val, isFinalSelection) => {
      if (type === 'origin') setOrigin(val);
      else setDestination(val);

      if (isFinalSelection) {
          saveToSession({ [type === 'origin' ? 'departure' : 'destination']: val });
      }
  };

  const handleDateChange = (type, val) => {
      setDates(prev => ({ ...prev, [type]: val }));
      
      if (val && val.length === 10) {
          saveToSession({ [type === 'start' ? 'from_date' : 'to_date']: val });
      }
  };

  const handleRoomChange = (val) => {
      const qty = parseInt(val);
      setRoomQty(qty);
      saveToSession({ room_qty: qty });
  };


  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setStep('SEARCH');
    setOutboundFlights([]);
    setHotels([]);
    setSelectedOutbound(null);
    setSelectedInbound(null);

    const flightsBody = {
      session_id: parseInt(sessionData?.id) || 0,
      departure: origin,
      arrival: destination,
      outbound_date: dates.start,
      return_date: dates.end,
      adults: travelerCounts.adults,
      children: travelerCounts.children,
      infants_in_seat: travelerCounts.infantsSeat,
      infants_on_lap: travelerCounts.infantsLap,
      stops: parseInt(maxStops),
      sort_by: parseInt(sortBy)
    };

    const childrenString = childAges.length > 0 ? childAges.join(",") : null;
    const hotelsBody = {
        session_id: parseInt(sessionData?.id) || 0,
        location: destination,
        search_type: "CITY",
        arrival_date: dates.start,
        departure_date: dates.end,
        adults: travelerCounts.adults,
        children: childrenString,
        room_qty: roomQty,
        price_min: null,
        price_max: null
    };

    try {
      const [flightRes, hotelRes] = await Promise.all([
        fetchWithAuth(`${API_BASE_URL}/search/getOutboundFlights`, flightsBody, "POST"),
        fetchWithAuth(`${API_BASE_URL}/search/getAccomodations`, hotelsBody, "POST")
      ]);

      if (flightRes.ok) {
        setOutboundFlights(await flightRes.json());
      }
      if (hotelRes.ok) {
        setHotels(await hotelRes.json());
      }
    } catch (err) {
      console.error(err);
      setError("Failed to fetch search results. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOutbound = async (flight) => {
    setSelectedOutbound(flight);
    setLoading(true);

    const flightsBody = {
        session_id: parseInt(sessionData?.id) || 0,
        token: flight.token,
        departure: origin,
        arrival: destination,
        outbound_date: dates.start,
        return_date: dates.end,
        adults: travelerCounts.adults,
        children: travelerCounts.children,
        infants_in_seat: travelerCounts.infantsSeat,
        infants_on_lap: travelerCounts.infantsLap,
    };

    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/search/getInboundFlights`, flightsBody, "POST");
      if (res.ok) {
        setInboundFlights(await res.json());
        setStep('SELECT_INBOUND');
      }
    } catch (err) {
      console.error(err);
      setError("Failed to find return flights.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectInbound = (flight) => {
    setSelectedInbound(flight);
    setStep('CONFIRM');
  };

  const handleViewDetails = async (hotel) => {
    setViewingHotel(hotel); 
    setLoadingDetails(true);
    setSelectedHotelDetails(null); 

    const childrenString = childAges.length > 0 ? childAges.join(",") : null;
    const detailsBody = {
        session_id: parseInt(sessionData?.id) || 0,
        loc_id: hotel.hotel_id,
        location: destination,
        search_type: "CITY",
        arrival_date: dates.start,
        departure_date: dates.end,
        adults: travelerCounts.adults,
        children: childrenString,
        room_qty: roomQty,
        price_min: null,
        price_max: null
    };

    try {
        const res = await fetchWithAuth(`${API_BASE_URL}/search/getHotelDetails`, detailsBody, "POST");
        if (res.ok) {
            const data = await res.json();
            setSelectedHotelDetails(data);
        }
    } catch (err) {
        console.error("Error fetching details:", err);
    } finally {
        setLoadingDetails(false);
    }
  };

  const handleBookTrip = async () => {
    const needsFlight = selectedInbound && !booked.flights;
    const needsHotel = selectedHotel && !booked.hotel;

    if (!needsFlight && !needsHotel) {
        if (!selectedHotel) setError("Please select an accommodation to continue.");
        return;
    }

    setLoading(true);
    setError(null);

    try {
        const bookingPromises = [];

        if (needsFlight) {
            const outboundSegments = selectedOutbound.flights;
            const destArrival = outboundSegments[outboundSegments.length - 1].arrival_time;

            const inboundSegments = selectedInbound.flights;
            const destDeparture = inboundSegments[0].departure_time;

            bookingPromises.push(
                fetchWithAuth(`${API_BASE_URL}/search/bookFlight`, {
                    session_id: parseInt(sessionData?.id) || 0,
                    token: selectedInbound.token,
                    departure: origin,
                    arrival: destination,
                    outbound_date: dates.start,
                    return_date: dates.end,
                    adults: travelerCounts.adults,
                    price: selectedInbound.price,
                    destination_arrival: destArrival,
                    destination_departure: destDeparture
                }, "POST").then(res => ({ type: 'flights', res }))
            );
        }

        if (needsHotel && selectedHotel.booking_url) {
            bookingPromises.push(
                fetchWithAuth(`${API_BASE_URL}/search/bookAccomodation`, {
                    session_id: parseInt(sessionData?.id),
                    booking_url: selectedHotel.booking_url,
                    price: selectedHotel.price,
                    currency: selectedHotel.currency
                }, "POST").then(res => ({ type: 'hotel', res }))
            );
        } else if (needsHotel) {
             console.error("Booking URL missing from selected hotel object.");
             setError("Missing hotel booking details. Please try viewing details again.");
             setLoading(false);
             return;
        }

        const results = await Promise.all(bookingPromises);
        let newBookedState = { ...booked };

        for (const item of results) {
            if (item.res.ok) {
                newBookedState[item.type] = true;
            } else {
                setError(`Failed to book ${item.type}. Please try again.`);
            }
        }

        setBooked(newBookedState);

        if (newBookedState.flights && newBookedState.hotel) {
            toast.success("Success! Flights and Accommodation booked. ✈️🏨");
            if (refreshContext) refreshContext();
            setTimeout(() => {
                navigate(`/plan/${sessionData.id}/itinerary`);
            }, 1000);
        } else if (newBookedState.flights && !newBookedState.hotel) {
            toast.success("Flights booked! Please proceed with hotel booking. ✈️");
            if (refreshContext) refreshContext();
        } else if (!newBookedState.flights && newBookedState.hotel) {
            toast.success("Accommodation booked! Please proceed with flights. 🏨");
            if (refreshContext) refreshContext();
        }

    } catch (err) {
        setError("Error during booking process.");
        console.error(err);
    } finally {
        setLoading(false);
    }
  };

  const resetSelection = () => {
    setStep('SEARCH');
    setSelectedOutbound(null);
    setSelectedInbound(null);
    setInboundFlights([]);
    setBooked({ flights: false, hotel: false });
    setSelectedHotel(null);
  };

  return (
    <PageTransition className="flex flex-col w-full h-full bg-gray-50 overflow-hidden">

      {viewingHotel && (
          <HotelDetailsModal 
            hotel={viewingHotel}
            details={selectedHotelDetails}
            isLoading={loadingDetails}
            onClose={() => setViewingHotel(null)} 
            onSelect={(hotelWithUrl) => {
                setSelectedHotel(hotelWithUrl);
                setViewingHotel(null);
            }}
          />
      )}

      {viewingFlight && (
          <FlightDetailsModal 
              flight={viewingFlight} 
              onClose={() => setViewingFlight(null)} 
          />
      )}

      <div className="bg-white border-b border-gray-200 p-4 shadow-sm shrink-0 flex flex-wrap gap-4 items-end z-20">
        <LocationAutocomplete 
            label="Origin"
            value={origin} 
            onChange={(val, isFinal) => handleLocationChange('origin', val, isFinal)} 
            placeholder="City, Country"
        />
        <LocationAutocomplete 
            label="Destination"
            value={destination} 
            onChange={(val, isFinal) => handleLocationChange('destination', val, isFinal)} 
            placeholder="City, Country"
        />
        <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Dates</label>
            <div className="flex items-center gap-2">
                <input 
                    type="date" 
                    value={dates.start} 
                    onChange={(e) => handleDateChange('start', e.target.value)} 
                    className="border border-gray-300 rounded-lg px-2 py-2 text-sm text-gray-700"
                />
                <input 
                    type="date" 
                    value={dates.end} 
                    onChange={(e) => handleDateChange('end', e.target.value)} 
                    className="border border-gray-300 rounded-lg px-2 py-2 text-sm text-gray-700"
                />
            </div>
        </div>
        
        <TravelersInput 
            counts={travelerCounts} 
            setCounts={setTravelerCounts} 
            childAges={childAges} 
            setChildAges={setChildAges} 
            onSave={saveToSession}
        />

        <div className="flex flex-col gap-1 w-20">
            <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Rooms</label>
            <select 
                value={roomQty} 
                onChange={(e) => handleRoomChange(e.target.value)} 
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-bold text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
                {Array.from({ length: Math.max(1, travelerCounts.adults) }, (_, i) => i + 1).map(num => (
                    <option key={num} value={num}>{num}</option>
                ))}
            </select>
        </div>

        <div className="flex gap-4 ml-auto border-l border-gray-200 pl-4">
            <div className="flex flex-col gap-1 w-32">
                <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Stops</label>
                <select 
                    value={maxStops} 
                    onChange={(e) => setMaxStops(e.target.value)} 
                    className="border border-gray-300 rounded-lg px-2 py-2 text-sm font-bold text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value={0}>Any Stops</option>
                    <option value={1}>Nonstop only</option>
                    <option value={2}>Up to 1 stop</option>
                </select>
            </div>
            
            <div className="flex flex-col gap-1 w-32">
                <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Sort By</label>
                <select 
                    value={sortBy} 
                    onChange={(e) => setSortBy(e.target.value)} 
                    className="border border-gray-300 rounded-lg px-2 py-2 text-sm font-bold text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value={1}>Best Flights</option>
                    <option value={2}>Lowest Price</option>
                    <option value={3}>Fastest</option>
                </select>
            </div>
        </div>

        <button 
          onClick={handleSearch}
          disabled={loading || !destination}
          className="h-10 px-6 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold shadow-md disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      <div className="flex-grow overflow-y-auto p-8 z-10">
        <div className="max-w-6xl mx-auto space-y-8">
          {error && <div className="bg-red-100 text-red-700 p-4 rounded-lg">{error}</div>}

          {(step === 'CONFIRM' || selectedHotel) && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center animate-in fade-in slide-in-from-top-4 duration-500">
                <h2 className="text-3xl font-bold text-green-800 mb-4">Trip Summary</h2>
                <div className="flex justify-center gap-8 text-left mb-8 flex-wrap">
                    {selectedOutbound && selectedInbound ? (
                        <>
                             <div className={`bg-white p-4 rounded shadow-sm w-64 border-l-4 ${booked.flights ? 'border-gray-400 opacity-75' : 'border-blue-500'}`}>
                                <div className="flex justify-between"><h3 className="font-bold text-gray-500 text-xs uppercase">Outbound</h3>{booked.flights && <span className="text-xs font-bold text-green-600 bg-green-100 px-2 rounded-full">BOOKED</span>}</div>
                                <div className="font-bold text-lg">{selectedOutbound.flights[0].airline}</div>
                                <div>{selectedOutbound.flights[0].departure_time} - {selectedOutbound.flights[0].arrival_time}</div>
                            </div>
                            <div className={`bg-white p-4 rounded shadow-sm w-64 border-l-4 ${booked.flights ? 'border-gray-400 opacity-75' : 'border-blue-500'}`}>
                                 <div className="flex justify-between"><h3 className="font-bold text-gray-500 text-xs uppercase">Return</h3>{booked.flights && <span className="text-xs font-bold text-green-600 bg-green-100 px-2 rounded-full">BOOKED</span>}</div>
                                <div className="font-bold text-lg">{selectedInbound.flights[0].airline}</div>
                                <div>{selectedInbound.flights[0].departure_time} - {selectedInbound.flights[0].arrival_time}</div>
                            </div>
                        </>
                    ) : (
                        <div className="bg-gray-100 border-2 border-dashed border-gray-300 p-4 rounded shadow-sm flex flex-col justify-center items-center w-64 opacity-50"><span className="text-gray-500 font-bold text-lg">No Flights Selected</span></div>
                    )}

                    {selectedHotel ? (
                        <div className={`bg-white p-4 rounded shadow-sm w-64 border-l-4 ${booked.hotel ? 'border-gray-400 opacity-75' : 'border-green-500'}`}>
                            <div className="flex justify-between"><h3 className="font-bold text-gray-500 text-xs uppercase">Accommodation</h3>{booked.hotel && <span className="text-xs font-bold text-green-600 bg-green-100 px-2 rounded-full">BOOKED</span>}</div>
                            <div className="font-bold text-lg truncate" title={selectedHotel.hotel_name}>{selectedHotel.hotel_name}</div>
                            <div className="text-sm text-gray-600">{roomQty} Room{roomQty > 1 ? 's' : ''}, {travelerCounts.adults} Adult{travelerCounts.adults > 1 ? 's' : ''}</div>
                            <div className="text-green-600 font-bold mt-1">{selectedHotel.price} {selectedHotel.currency}</div>
                        </div>
                    ) : (
                        <div className="bg-orange-50 border-2 border-dashed border-orange-300 p-4 rounded shadow-sm flex flex-col justify-center items-center w-64">
                            <span className="text-orange-600 font-bold text-lg mb-1">No Hotel Yet</span>
                            <p className="text-xs text-orange-500 text-center">Select a hotel below.</p>
                        </div>
                    )}
                </div>
                
                <div className="flex justify-center gap-4">
                    <button onClick={resetSelection} className="px-6 py-3 text-gray-600 font-bold hover:bg-gray-100 rounded-lg">Reset All</button>
                    <button 
                        onClick={handleBookTrip} 
                        disabled={loading || (booked.flights && booked.hotel)} 
                        className={`px-8 py-3 font-bold rounded-lg shadow-lg transform transition ${loading || (booked.flights && booked.hotel) ? "bg-gray-400 cursor-not-allowed text-gray-100" : "bg-green-600 text-white hover:bg-green-700 hover:-translate-y-1"}`}
                    >
                        {loading ? "Processing..." : "Confirm & Book Selected"}
                    </button>
                </div>
            </div>
          )}

          {(step === 'SEARCH' || step === 'SELECT_INBOUND') && (
            <section>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold text-gray-800">
                        {step === 'SEARCH' && outboundFlights.length === 0 
                            ? 'Flights' 
                            : step === 'SEARCH' 
                                ? '1. Select Outbound Flight' 
                                : '2. Select Return Flight'}
                    </h2>
                    {step === 'SELECT_INBOUND' && <button onClick={resetSelection} className="text-sm text-red-500 font-bold hover:underline">Change Outbound</button>}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {(step === 'SEARCH' ? outboundFlights : inboundFlights).map((flight, idx) => (
                        <FlightCard 
                            key={idx} 
                            flight={flight} 
                            onSelect={() => step === 'SEARCH' ? handleSelectOutbound(flight) : handleSelectInbound(flight)} 
                            onViewDetails={() => setViewingFlight(flight)}
                            btnText={step === 'SEARCH' ? "Select Outbound" : "Select Return"} 
                            isOutbound={step === 'SEARCH'}
                        />
                    ))}
                    {(step === 'SEARCH' ? outboundFlights : inboundFlights).length === 0 && !loading && <div className="col-span-2 text-center py-10 text-gray-400 border-2 border-dashed rounded-xl">No flights found.</div>}
                </div>
            </section>
          )}

          <section className="mt-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Accommodations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {hotels.map((hotel) => (
                    <HotelCard 
                        key={hotel.hotel_id} 
                        hotel={hotel} 
                        isSelected={selectedHotel?.hotel_id === hotel.hotel_id}
                        onSelect={() => handleViewDetails(hotel)} 
                    />
                ))}
                {hotels.length === 0 && !loading && <div className="col-span-full text-center py-10 text-gray-400 border-2 border-dashed rounded-xl">No hotels found.</div>}
            </div>
          </section>

        </div>
      </div>
    </PageTransition>
  );
}

function FlightCard({ flight, onSelect, onViewDetails, btnText, isOutbound }) {
    const segments = flight.flights;
    const firstLeg = segments[0];
    const lastLeg = segments[segments.length - 1];
    
    let totalFlightMinutes = 0;
    let totalLayoverMinutes = 0;
    const layovers = [];

    segments.forEach((segment, i) => {
        totalFlightMinutes += parseInt(segment.duration) || 0;

        if (i < segments.length - 1) {
            const nextSegment = segments[i + 1];
            
            const arrival = new Date(segment.arrival_time.replace(" ", "T"));
            const departure = new Date(nextSegment.departure_time.replace(" ", "T"));
            
            const diffMins = Math.floor((departure - arrival) / 60000);
            
            if (diffMins > 0) {
                totalLayoverMinutes += diffMins;
                layovers.push({
                    city: segment.arrival.split(',')[0],
                    code: segment.arrival.split('(')[1]?.replace(')', '') || '',
                    duration: diffMins
                });
            }
        }
    });

    const totalDurationMinutes = totalFlightMinutes + totalLayoverMinutes;
    
    const formatDuration = (mins) => {
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        return `${h}h ${m}m`;
    };

    return (
      <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition group">

        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3 mt-1">
             {firstLeg.airline_logo && <img src={firstLeg.airline_logo} alt={firstLeg.airline} className="h-8 w-8 object-contain" />}
             <div>
                 <div className="font-bold text-lg text-gray-800 leading-none">{firstLeg.airline}</div>
                 {segments.length > 1 && segments[0].airline !== segments[1].airline && (
                     <div className="text-[10px] text-gray-400 mt-1">Includes {segments[1].airline}</div>
                 )}
             </div>
          </div>
          <div className="text-right flex flex-col items-end justify-center">
              <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-0.5">
                  {isOutbound ? "Est. Total" : "Total Price"}
              </span>
              <div className="text-blue-600 font-bold text-2xl leading-none">{flight.price} <span className="text-lg">{flight.currency}</span></div>
          </div>
        </div>

        <div className="flex justify-between items-center text-sm text-gray-600 mb-4 bg-gray-50 p-4 rounded-lg">

          <div>
              <div className="font-bold text-gray-900 text-lg">{firstLeg.departure_time.split(" ")[1]}</div>
              <div className="text-gray-500 font-medium">{firstLeg.departure.split(',')[0]}</div>
          </div>

          <div className="flex flex-col items-center px-4 flex-grow">
             <span className="text-xs text-gray-500 font-bold mb-1">{formatDuration(totalDurationMinutes)}</span>
             
             <div className="w-full flex items-center gap-1">
                 <div className="h-[2px] bg-gray-300 flex-grow relative">
                    {layovers.map((_, idx) => (
                        <div key={idx} className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-white border-2 border-gray-400 rounded-full"></div>
                    ))}
                 </div>
                 <span className="text-gray-400">✈</span>
             </div>

             <span className={`text-[10px] font-bold mt-1 ${layovers.length > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                {layovers.length === 0 ? "Direct" : `${layovers.length} Stop${layovers.length > 1 ? 's' : ''}`}
             </span>
          </div>

          <div className="text-right">
              <div className="font-bold text-gray-900 text-lg">{lastLeg.arrival_time.split(" ")[1]}</div>
              <div className="text-gray-500 font-medium">{lastLeg.arrival.split(',')[0]}</div>
          </div>
        </div>

        {layovers.length > 0 && (
            <div className="mb-4 text-xs bg-orange-50 border border-orange-100 p-2 rounded text-orange-800">
                {layovers.map((stop, i) => (
                    <div key={i} className="flex gap-1">
                        <span className="font-bold">Stop in {stop.city}:</span>
                        <span>{formatDuration(stop.duration)} layover</span>
                    </div>
                ))}
            </div>
        )}

        <div className="flex gap-2 mt-4">
            <button onClick={onViewDetails} className="w-1/3 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-100 font-bold text-sm transition">
                Details
            </button>
            <button onClick={onSelect} className="w-2/3 py-2 rounded-lg border border-blue-100 bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white font-black text-sm transition">
                {btnText}
            </button>
        </div>
      </div>
    );
}
  
function HotelCard({ hotel, onSelect, isSelected }) {
    return (
      <div 
        className={`bg-white rounded-xl border-2 shadow-sm transition overflow-hidden flex flex-col h-[400px] cursor-pointer group ${isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-transparent hover:shadow-lg'}`}
        onClick={onSelect}
      >
        <div className="h-40 w-full relative overflow-hidden">
             {hotel.photo_urls?.[0] ? (
                 <img src={hotel.photo_urls[0]} alt="Hotel" className="h-full w-full object-cover group-hover:scale-105 transition duration-500" />
             ) : (
                <div className="h-full w-full bg-gray-200 flex items-center justify-center text-gray-400">No Image</div>
             )}
             <div className="absolute top-2 left-2 bg-white/90 backdrop-blur px-2 py-0.5 rounded text-[10px] font-bold shadow-sm">{"⭐".repeat(hotel.propertyClass || 0)}</div>
             <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"></div>
             <div className="absolute bottom-3 left-3 text-white"><div className="font-bold text-lg drop-shadow-md line-clamp-1">{hotel.hotel_name}</div></div>
        </div>
        <div className="p-4 flex flex-col flex-grow bg-white">
          <div className="flex items-center gap-2 mb-2">
             {hotel.reviewScore && <span className="bg-blue-700 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">{hotel.reviewScore}</span>}
             <span className="text-xs font-bold text-gray-800">{hotel.reviewScoreWord}</span>
             <span className="text-[10px] text-gray-400">({hotel.reviewCount} reviews)</span>
          </div>
          <p className="text-[11px] text-gray-500 line-clamp-2 italic mb-3">"{hotel.accessibilityLabel}"</p>
          <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="bg-gray-50 p-1.5 rounded border border-gray-100"><div className="text-[9px] uppercase text-gray-400 font-bold">Check-in</div><div className="text-[10px] font-medium text-gray-700">{hotel.checkin_time_range || "Flexible"}</div></div>
              <div className="bg-gray-50 p-1.5 rounded border border-gray-100"><div className="text-[9px] uppercase text-gray-400 font-bold">Check-out</div><div className="text-[10px] font-medium text-gray-700">{hotel.checkout_time_range || "Flexible"}</div></div>
          </div>
          <div className="mt-auto pt-3 border-t border-gray-100 flex justify-between items-center">
              <div><div className="text-[10px] text-gray-400">Total Price</div><div className="text-lg font-bold text-blue-700">{hotel.price} {hotel.currency}</div></div>
              
              <button 
                onClick={(e) => {
                    e.stopPropagation();
                    onSelect();
                }}
                className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg text-sm font-bold hover:bg-blue-600 hover:text-white transition"
              >
                 View Details
              </button>
          </div>
        </div>
      </div>
    );
}
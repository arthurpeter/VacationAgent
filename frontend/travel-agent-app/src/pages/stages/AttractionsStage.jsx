import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  MapPin, Loader2, ArrowRight, Sparkles, Search, Plus, Check, 
  Calendar, Trash2, Clock, Star, Trophy, Smile, X, ExternalLink, Info, Banknote, Map as MapIcon, ChevronDown 
} from 'lucide-react';

import { fetchWithAuth } from '../../authService'; 
import { API_BASE_URL } from '../../config';
import PageTransition from '../../components/PageTransition';

// --- SHARED UTILS ---
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

// --- SUB-COMPONENTS ---
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
        if (err.name !== 'AbortError') console.error(err);
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
  }, []);

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
    <div className="flex flex-col gap-1 w-48 sm:w-56 relative" ref={wrapperRef}>
      <label className="text-[10px] uppercase text-gray-400 font-bold tracking-wider ml-1">{label}</label>
      <div className="relative">
        <div className="absolute left-3 top-2.5 text-blue-600">
          <MapPin size={16} />
        </div>
        <input 
          value={value}
          onChange={handleInput}
          placeholder={placeholder}
          className="bg-gray-50 border border-gray-200 rounded-xl pl-10 pr-10 py-2 text-xs font-black text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full transition-all"
        />
        <div className="absolute right-3 top-2">
          {isLoading ? <Loader2 size={14} className="animate-spin text-blue-600" /> : <ChevronDown size={14} className="text-gray-300" />}
        </div>
      </div>
      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute top-full left-0 right-0 append-to-body bg-white border border-gray-100 rounded-2xl shadow-2xl mt-2 z-[110] max-h-60 overflow-y-auto p-2 animate-fadeIn">
          {suggestions.map((item, idx) => (
            <li 
              key={idx} 
              onClick={() => selectSuggestion(item)}
              className="px-4 py-3 hover:bg-blue-50 cursor-pointer rounded-xl flex flex-col border-b border-gray-50 last:border-0"
            >
              <span className="font-bold text-sm text-gray-800">{item.address.city || item.name}</span>
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">{item.address.country}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const DiscoveryCard = ({ poi, isAdded, onAdd, onShowDetails, isUpdating }) => {
  const [bucket, setBucket] = useState('want');
  const [time, setTime] = useState(poi.recommended_duration_mins || 120);

  return (
    <div className={`flex flex-col p-5 rounded-3xl border transition-all ${isAdded ? 'bg-green-50/30 border-green-200' : 'bg-white border-gray-100 hover:border-blue-200 shadow-sm'}`}>
      <div className="flex items-start gap-5">
        <div className="relative w-28 h-28 flex-shrink-0">
          {poi.image_url ? (
            <img src={poi.image_url} alt="" className="w-full h-full object-cover rounded-2xl border border-gray-100 shadow-sm" loading="lazy" />
          ) : (
            <div className="w-full h-full bg-gray-100 rounded-2xl flex items-center justify-center text-3xl">🏛️</div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start mb-1">
            <h4 className="font-black text-gray-900 text-lg leading-tight truncate pr-4">{poi.official_name}</h4>
            <div className="flex flex-shrink-0 gap-2">
               {poi.rating && <span className="text-[10px] font-black bg-orange-100 text-orange-600 px-2 py-1 rounded-lg">⭐ {poi.rating}</span>}
               {poi.price_tier && <span className="text-[10px] font-black bg-green-100 text-green-600 px-2 py-1 rounded-lg">{'€'.repeat(poi.price_tier)}</span>}
            </div>
          </div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md uppercase tracking-wider">{poi.category}</span>
            <span className="text-[10px] text-gray-400 font-medium italic truncate">{poi.formatted_address || poi.city}</span>
          </div>
          <p className="text-xs text-gray-500 line-clamp-2 mb-4 leading-relaxed">{poi.description}</p>
          <div className="flex flex-wrap gap-3 items-center">
            <button onClick={() => onShowDetails(poi)} className="text-[10px] font-black uppercase tracking-wider text-gray-400 hover:text-blue-600 flex items-center gap-1 transition-colors">
              <Info size={14} /> Full Info
            </button>
            {!isAdded && (
              <div className="flex flex-wrap gap-3 items-end ml-auto">
                <div className="flex bg-gray-100 p-1 rounded-xl border border-gray-200/50">
                  {[
                    { id: 'must', icon: Trophy, color: 'text-orange-500' },
                    { id: 'want', icon: Star, color: 'text-blue-500' },
                    { id: 'optional', icon: Smile, color: 'text-emerald-500' }
                  ].map(b => (
                    <button 
                      key={b.id}
                      onClick={() => setBucket(b.id)}
                      className={`p-2 rounded-lg transition-all ${bucket === b.id ? 'bg-white shadow-sm scale-110' : 'opacity-40 hover:opacity-100'}`}
                    >
                      <b.icon size={14} className={b.color} />
                    </button>
                  ))}
                </div>
                <div className="relative w-24">
                  <Clock size={12} className="absolute left-3 top-2.5 text-gray-400" />
                  <input 
                    type="number" 
                    className="w-full bg-gray-100 border border-gray-200/50 rounded-xl pl-8 pr-2 py-2 text-xs font-bold focus:ring-2 focus:ring-blue-500 outline-none"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                  />
                </div>
                <button 
                  onClick={() => onAdd(poi, bucket, time)}
                  disabled={isUpdating === poi.id}
                  className="bg-blue-600 text-white p-2.5 rounded-xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-200"
                >
                  {isUpdating === poi.id ? <Loader2 size={18} className="animate-spin" /> : <Plus size={18} />}
                </button>
              </div>
            )}
            {isAdded && (
              <div className="flex items-center gap-2 text-green-600 font-bold text-xs bg-green-100/50 w-fit px-4 py-2 rounded-xl ml-auto border border-green-200">
                <Check size={14} /> Saved
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// --- MAIN STAGE COMPONENT ---

export default function AttractionsStage({ gameState, session, onFinalize }) {
  const sessionId = session?.id;

  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isUpdatingBucket, setIsUpdatingBucket] = useState(null);
  const [discoveryResults, setDiscoveryResults] = useState(gameState.resolved_attractions || []); 
  const [itinerary, setItinerary] = useState(gameState.pois || []); 
  const [searchQuery, setSearchQuery] = useState("");
  const [activeDetails, setActiveDetails] = useState(null);
  const [searchLocation, setSearchLocation] = useState(gameState.search_location || session?.destination || "");

  const initialFetchPerformed = useRef(false);

  const handleSearch = useCallback(async (e, forcedAction = "custom_search") => {
    if (e) e.preventDefault();
    setIsSearching(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/attractions/search`, {
          session_id: sessionId,
          query: searchQuery || "",
          action: forcedAction
      }, "POST");
      if (res && res.ok) {
        const data = await res.json();
        setDiscoveryResults(data.resolved_attractions || []);
      }
    } catch (err) { 
        console.error(err); 
    } finally {
      setIsSearching(false);
      setIsLoading(false);
    }
  }, [sessionId, searchQuery]);

  useEffect(() => {
    const checkInitialFetch = async () => {
        if (!discoveryResults.length && !itinerary.length && !initialFetchPerformed.current) {
            initialFetchPerformed.current = true;
            await handleSearch(null, "initial_fetch");
        }
    };
    checkInitialFetch();
  }, [discoveryResults.length, itinerary.length, handleSearch]);

  const handleLocationChange = async (newVal, isSelection) => {
    setSearchLocation(newVal);
    if (isSelection) {
      setIsSearching(true);
      try {
        const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/update-search-location`, {
          session_id: sessionId,
          new_location: newVal
        }, "POST");
        if (res && res.ok) {
          await handleSearch(null, "initial_fetch");
        }
      } catch (err) {
        console.error("Location switch error", err);
      } finally {
        setIsSearching(false);
      }
    }
  };

  const handleAddToBucket = async (attraction, bucket, time) => {
    setIsUpdatingBucket(attraction.id);
    try {
      const payload = {
        session_id: sessionId,
        attraction_id: attraction.id,
        name: attraction.official_name,
        image_url: attraction.image_url || "",
        time_to_spend: parseInt(time) || 120,
        bucket: bucket,
        location: [
          attraction.city,
          attraction.country
        ]
          .filter(Boolean)
          .join(", ")
      };
      const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/attractions/add-to-bucket`, payload, "POST");
      if (res && res.ok) {
        const data = await res.json();
        setItinerary(data.pois || []);
      }
    } catch (err) { console.error(err); } finally {
      setIsUpdatingBucket(null);
    }
  };

  const renderDetailsModal = () => {
    if (!activeDetails) return null;
    const p = activeDetails;
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/80 backdrop-blur-md animate-fadeIn" onClick={() => setActiveDetails(null)}>
        <div className="bg-white w-full max-w-2xl rounded-[3rem] overflow-hidden shadow-2xl flex flex-col max-h-[85vh]" onClick={e => e.stopPropagation()}>
          <div className="relative h-64 flex-shrink-0">
            <img src={p.image_url || 'https://via.placeholder.com/800x600?text=No+Image'} className="w-full h-full object-cover" alt="" />
            <button onClick={() => setActiveDetails(null)} className="absolute top-6 right-6 p-3 bg-black/20 backdrop-blur-xl rounded-full text-white hover:bg-black/40 transition-all">
              <X size={20} />
            </button>
            <div className="absolute bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-gray-900 via-gray-900/20 to-transparent text-white">
              <div className="flex items-center gap-2 mb-2">
                 <span className="bg-blue-600 text-[10px] font-black uppercase px-2 py-1 rounded-md">{p.category}</span>
                 {p.rating && <span className="bg-orange-500 text-[10px] font-black uppercase px-2 py-1 rounded-md">⭐ {p.rating}</span>}
              </div>
              <h2 className="text-3xl font-black">{p.official_name}</h2>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
            <div>
               <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-4">Operating Hours</h4>
               <div className="grid grid-cols-2 gap-x-12 gap-y-3 bg-gray-50 p-6 rounded-[2rem]">
                  {p.opening_hours ? Object.entries(p.opening_hours).map(([day, hours]) => (
                    <div key={day} className="flex justify-between items-center border-b border-gray-200 pb-1 last:border-0">
                      <span className="text-[10px] font-black text-gray-400 uppercase">{day}</span>
                      <span className="text-xs font-black text-gray-800">{hours}</span>
                    </div>
                  )) : (
                    <p className="text-xs text-gray-400 italic">No hours data available.</p>
                  )}
               </div>
            </div>
            <div>
               <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Description</h4>
               <p className="text-gray-600 leading-relaxed text-sm">{p.description || "No detailed description available."}</p>
            </div>
            <div className="grid grid-cols-2 gap-6 bg-gray-100 p-6 rounded-2xl">
               <div className="space-y-1">
                  <p className="text-[10px] font-black text-gray-400 uppercase">Location</p>
                  <p className="font-bold text-gray-800 text-xs flex items-center gap-1 truncate"><MapIcon size={12} className="text-blue-500"/> {p.city}, {p.country}</p>
               </div>
               <div className="space-y-1">
                  <p className="text-[10px] font-black text-gray-400 uppercase">Price Level</p>
                  <p className="font-bold text-gray-800 text-xs flex items-center gap-1"><Banknote size={12} className="text-green-500"/> {p.price_tier ? '€'.repeat(p.price_tier) : 'Varies'}</p>
               </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <PageTransition className="w-full h-full overflow-hidden bg-gray-50 p-6 md:p-8 relative flex flex-col">
      {renderDetailsModal()}
      
      {/* NEW FLOATING STEP NAVIGATION CONTAINER
        This sits completely on top of everything without a white structural layout bar.
        Backdrop-blur-md creates the luxury transparent grey element, turning solid charcoal on hover.
      */}
      <div className="absolute top-3 left-8 right-8 z-[100] pointer-events-auto flex items-center justify-between">
    
          {/* Left: location controls */}
          <div className="flex items-center gap-4">
              <LocationAutocomplete 
                  label="City to search in"
                  value={searchLocation}
                  onChange={handleLocationChange}
                  placeholder="Change location..."
              />
              <div className="h-7 w-px bg-gray-200 mt-4" />
              <div className="flex flex-col mt-3">
                  <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1 ml-1">Trip Base</span>
                  <div className="flex items-center gap-2 text-xs font-black text-gray-700 bg-white border border-gray-100 px-3.5 py-1.5 rounded-xl shadow-sm">
                      <MapIcon size={12} className="text-blue-600" /> {session?.destination}
                  </div>
              </div>
          </div>

          {/* Right: finalize button */}
          <button 
              onClick={onFinalize}
              className="px-4 py-1.5 bg-transparent text-gray-400 hover:text-blue-500 rounded-2xl font-black text-xs uppercase tracking-wider flex items-center gap-2 transition-all duration-300 group"
          >
              <span>Finalize Selection</span>
              <ArrowRight size={14} className="transform transition-transform group-hover:translate-x-1" />
          </button>
      </div>

      {/* FULL-HEIGHT SCREEN WRAPPER */}
      <div className="w-full flex-1 flex flex-col gap-6 min-h-0 pt-16">

        {/* COLUMNS LAYOUT CONTAINER */}
        <div className="flex flex-col lg:flex-row gap-8 flex-1 min-h-0 overflow-hidden">
          
          {/* FEED COLUMN */}
          <div className="flex-1 flex flex-col min-w-0 bg-white rounded-[2.5rem] border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b bg-white shrink-0">
              <form onSubmit={handleSearch} className="flex gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-5 top-4 text-gray-400" size={20} />
                  <input 
                    type="text" 
                    placeholder="Search vibes, categories, or specific places..."
                    className="w-full pl-14 pr-4 py-4 rounded-[1.5rem] border border-gray-200 outline-none text-sm font-medium focus:ring-2 focus:ring-blue-500 transition-all"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <button disabled={isSearching} className="bg-blue-600 text-white px-8 py-4 rounded-[1.5rem] font-black text-sm shadow-xl shadow-blue-200 hover:bg-blue-700 transition-all flex items-center gap-2">
                  {isSearching ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />} AI Discovery
                </button>
              </form>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar text-gray-800">
              {discoveryResults.map(poi => (
                <DiscoveryCard 
                  key={poi.id} 
                  poi={poi} 
                  isAdded={itinerary.some(p => String(p.id) === String(poi.id))}
                  onAdd={handleAddToBucket}
                  onShowDetails={setActiveDetails}
                  isUpdating={isUpdatingBucket}
                />
              ))}
              {!discoveryResults.length && !isSearching && (
                  <div className="h-full flex flex-col items-center justify-center opacity-20 py-20">
                    <Search size={64} className="mb-4" />
                    <p className="font-bold text-lg text-center text-gray-900">Your discovery feed is empty.<br/><span className="text-sm font-normal">Use the search above to unlock the magic of {searchLocation.split(',')[0]}.</span></p>
                  </div>
              )}
            </div>
          </div>

          {/* BUCKET COLUMN */}
          <div className="w-full lg:w-96 flex flex-col gap-4 bg-gray-900 rounded-[3rem] p-8 text-white shadow-2xl relative overflow-hidden shrink-0">
            <div className="absolute top-0 right-0 w-48 h-48 bg-blue-600/20 rounded-full -mr-24 -mt-24 blur-3xl" />
            <div className="relative z-10 flex items-center justify-between mb-8">
              <div>
                <h3 className="font-black text-2xl tracking-tight leading-none">Your Bucket</h3>
                <p className="text-gray-500 text-[10px] mt-2 font-black uppercase tracking-widest">{itinerary.length} STOPS SELECTED</p>
              </div>
              <div className="bg-gray-800 p-4 rounded-3xl border border-gray-700">
                <Calendar className="text-blue-400" size={24} />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-10 pr-2 custom-scrollbar relative z-10">
              {['must', 'want', 'optional'].map(category => {
                const items = itinerary.filter(i => i.bucket === category);
                if (!items.length) return null;
                return (
                  <div key={category} className="space-y-5">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-gray-500 flex items-center gap-3">
                      <div className={`w-2.5 h-2.5 rounded-full ${category === 'must' ? 'bg-orange-500 shadow-[0_0_12px_rgba(249,115,22,0.6)]' : category === 'want' ? 'bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.6)]' : 'bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.6)]'}`} />
                      {category === 'must' ? 'Non-Negotiables' : category === 'want' ? 'High Interest' : 'Bonus Stops'}
                    </h4>
                    <div className="space-y-4">
                      {items.map(item => (
                        <div key={item.id} className="bg-white/5 border border-white/10 p-4 rounded-3xl flex items-center gap-5 group hover:bg-white/10 transition-all">
                          <div className="w-12 h-12 rounded-xl overflow-hidden flex-shrink-0 bg-gray-800 border border-white/5">
                            {item.image_url ? <img src={item.image_url} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-xl">📍</div>}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-xs truncate leading-tight mb-1">{item.name}</p>
                            <p className="text-[10px] text-gray-400 font-black uppercase tracking-tighter">{item.time_to_spend} MINS</p>
                          </div>
                          <button className="text-gray-600 hover:text-red-400 transition-all opacity-0 group-hover:opacity-100 p-2">
                            <Trash2 size={18} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      </div>
    </PageTransition>
  );
}
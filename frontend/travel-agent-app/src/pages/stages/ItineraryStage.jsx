import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import { 
  MapPin, Loader2, ArrowRight, Sparkles, Search, Plus, Check, 
  Calendar, Trash2, Clock, Star, Trophy, Smile, X, ExternalLink, Info, Banknote, Map as MapIcon
} from 'lucide-react';

import { fetchWithAuth } from '../../authService'; 
import { API_BASE_URL } from '../../config';
import PageTransition from '../../components/PageTransition';

// --- SUB-COMPONENT: DISCOVERY CARD ---
const DiscoveryCard = ({ poi, isAdded, onAdd, onShowDetails, isUpdating }) => {
  const [bucket, setBucket] = useState('want');
  const [time, setTime] = useState(poi.recommended_duration_mins || 120);

  return (
    <div className={`flex flex-col p-5 rounded-3xl border transition-all ${isAdded ? 'bg-green-50/30 border-green-200' : 'bg-white border-gray-100 hover:border-blue-200 shadow-sm'}`}>
      <div className="flex items-start gap-5">
        <div className="relative w-28 h-28 flex-shrink-0">
          {poi.image_url ? (
            <img 
              src={poi.image_url} 
              alt="" 
              className="w-full h-full object-cover rounded-2xl border border-gray-100 shadow-sm" 
              loading="lazy" 
            />
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
            <button 
              onClick={() => onShowDetails(poi)}
              className="text-[10px] font-black uppercase tracking-wider text-gray-400 hover:text-blue-600 flex items-center gap-1 transition-colors"
            >
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

// --- MAIN COMPONENT ---
export default function ItineraryStage() {
  const { sessionData } = useOutletContext();
  const session = sessionData?.data || sessionData;
  const sessionId = session?.id;

  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [isUpdatingBucket, setIsUpdatingBucket] = useState(null);
  const [discoveryResults, setDiscoveryResults] = useState([]); 
  const [itinerary, setItinerary] = useState([]); 
  const [searchQuery, setSearchQuery] = useState("");
  const [activeDetails, setActiveDetails] = useState(null);

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
    } catch (err) { console.error(err); } finally {
      setIsSearching(false);
      setIsLoading(false);
    }
  }, [sessionId, searchQuery]);

  const refreshGlobalState = useCallback(async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/state/${sessionId}`, {}, "GET");
      if (res && res.ok) {
        const data = await res.json();
        setItinerary(data.pois || []);
        setDiscoveryResults(data.resolved_attractions || []);
        
        if (!data.resolved_attractions?.length && !data.pois?.length && !initialFetchPerformed.current) {
          initialFetchPerformed.current = true;
          await handleSearch(null, "initial_fetch");
        } else {
          setIsLoading(false);
        }
      }
    } catch (err) { setIsLoading(false); }
  }, [sessionId, handleSearch]);

  useEffect(() => {
    if (sessionId) refreshGlobalState();
  }, [sessionId, refreshGlobalState]);

  const handleAddToBucket = async (attraction, bucket, time) => {
    setIsUpdatingBucket(attraction.id);
    try {
      const payload = {
        session_id: sessionId,
        attraction_id: attraction.id,
        name: attraction.official_name,
        image_url: attraction.image_url || "",
        time_to_spend: parseInt(time) || 120,
        bucket: bucket 
      };

      const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/attractions/add-to-bucket`, payload, "POST");
      
      if (res && res.ok) {
        const data = await res.json();
        setItinerary(data.pois || []);
      } else {
        // If it's a 422, log the detail
        const err = await res.json();
        console.error("Bucket Update 422 Detail:", err);
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
          <div className="relative h-72 flex-shrink-0">
            <img src={p.image_url || 'https://via.placeholder.com/800x600?text=No+Image'} className="w-full h-full object-cover" alt="" />
            <button onClick={() => setActiveDetails(null)} className="absolute top-6 right-6 p-3 bg-black/20 backdrop-blur-xl rounded-full text-white hover:bg-black/40 transition-all">
              <X size={20} />
            </button>
            <div className="absolute bottom-0 left-0 right-0 p-10 bg-gradient-to-t from-gray-900 via-gray-900/20 to-transparent text-white">
              <div className="flex items-center gap-2 mb-2">
                 <span className="bg-blue-600 text-[10px] font-black uppercase px-2 py-1 rounded-md">{p.category}</span>
                 {p.rating && <span className="bg-orange-500 text-[10px] font-black uppercase px-2 py-1 rounded-md">⭐ {p.rating}</span>}
              </div>
              <h2 className="text-4xl font-black">{p.official_name}</h2>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-10 space-y-8 custom-scrollbar">
            <div>
               <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Description</h4>
               <p className="text-gray-600 leading-relaxed">{p.description || "No detailed description available."}</p>
            </div>
            <div className="grid grid-cols-2 gap-6 bg-gray-50 p-8 rounded-[2rem]">
               <div className="space-y-1">
                  <p className="text-[10px] font-black text-gray-400 uppercase">Location</p>
                  <p className="font-bold text-gray-800 flex items-center gap-1"><MapIcon size={14} className="text-blue-500"/> {p.city}, {p.country}</p>
               </div>
               <div className="space-y-1">
                  <p className="text-[10px] font-black text-gray-400 uppercase">Best Time</p>
                  <p className="font-bold text-gray-800 flex items-center gap-1"><Clock size={14} className="text-orange-500"/> {p.tod_preference || 'Flexible'}</p>
               </div>
               <div className="space-y-1">
                  <p className="text-[10px] font-black text-gray-400 uppercase">Estimated Price</p>
                  <p className="font-bold text-gray-800 flex items-center gap-1"><Banknote size={14} className="text-green-500"/> {p.price_tier ? '€'.repeat(p.price_tier) : 'Variable'}</p>
               </div>
               <div className="space-y-1">
                  <p className="text-[10px] font-black text-gray-400 uppercase">Official Website</p>
                  {p.website_url ? <a href={p.website_url} target="_blank" rel="noreferrer" className="text-blue-600 font-bold hover:underline flex items-center gap-1">Visit Site <ExternalLink size={12}/></a> : <p className="text-gray-400 font-bold">Unavailable</p>}
               </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) return (
    <div className="h-full w-full flex items-center justify-center bg-white">
      <Loader2 className="animate-spin text-blue-600" size={40} />
    </div>
  );

  return (
    <PageTransition className="w-full h-full overflow-y-auto bg-gray-50 p-4 md:p-8 relative">
      {renderDetailsModal()}
      
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row gap-8 h-[calc(100vh-160px)]">
        <div className="flex-1 flex flex-col min-w-0">
          <div className="bg-white rounded-[2.5rem] border border-gray-200 shadow-sm flex flex-col overflow-hidden h-full">
            <div className="p-8 border-b bg-white">
              <form onSubmit={(e) => handleSearch(e)} className="flex gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-5 top-4 text-gray-400" size={20} />
                  <input 
                    type="text" 
                    placeholder="Search landmarks or specific vibes..."
                    className="w-full pl-14 pr-4 py-4 rounded-[1.5rem] border border-gray-200 outline-none text-sm focus:ring-2 focus:ring-blue-500 transition-all"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <button disabled={isSearching} className="bg-blue-600 text-white px-8 py-4 rounded-[1.5rem] font-black text-sm shadow-xl shadow-blue-200 hover:bg-blue-700 transition-all flex items-center gap-2">
                  {isSearching ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />} Search
                </button>
              </form>
            </div>

            <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar">
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
              {discoveryResults.length === 0 && !isSearching && (
                  <div className="h-full flex flex-col items-center justify-center opacity-20 py-20">
                      <Search size={64} className="mb-4" />
                      <p className="font-bold">No results found for your search.</p>
                  </div>
              )}
            </div>
          </div>
        </div>

        <div className="w-full lg:w-96 flex flex-col gap-4">
          <div className="bg-gray-900 rounded-[3rem] p-10 text-white flex flex-col h-full shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-48 h-48 bg-blue-600/20 rounded-full -mr-24 -mt-24 blur-3xl" />
            <div className="relative z-10 flex items-center justify-between mb-10">
              <div>
                <h3 className="font-black text-3xl tracking-tight leading-none">Your Trip</h3>
                <p className="text-gray-500 text-[10px] mt-3 font-black uppercase tracking-widest leading-none">{itinerary.length} STOPS SELECTED</p>
              </div>
              <div className="bg-gray-800 p-4 rounded-3xl border border-gray-700">
                <Calendar className="text-blue-400" size={28} />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-10 pr-2 custom-scrollbar relative z-10">
              {['must', 'want', 'optional'].map(category => {
                const items = itinerary.filter(i => i.bucket === category);
                if (items.length === 0) return null;
                return (
                  <div key={category} className="space-y-5">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-gray-500 flex items-center gap-3">
                      <div className={`w-2.5 h-2.5 rounded-full ${category === 'must' ? 'bg-orange-500 shadow-[0_0_12px_rgba(249,115,22,0.6)]' : category === 'want' ? 'bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.6)]' : 'bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.6)]'}`} />
                      {category === 'must' ? 'Non-Negotiables' : category === 'want' ? 'High Interest' : 'Bonus Stops'}
                    </h4>
                    <div className="space-y-4">
                      {items.map(item => (
                        <div key={item.id} className="bg-white/5 border border-white/10 p-4 rounded-3xl flex items-center gap-5 group hover:bg-white/10 transition-all">
                          <div className="w-14 h-14 rounded-2xl overflow-hidden flex-shrink-0 bg-gray-800 border border-white/5">
                            {item.image_url ? <img src={item.image_url} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-xl">📍</div>}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-sm truncate leading-tight mb-1">{item.name}</p>
                            <p className="text-[10px] text-gray-500 font-black uppercase tracking-tighter">{item.time_to_spend} MINS</p>
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

            <button disabled={itinerary.length === 0} className="relative z-10 mt-10 w-full py-6 bg-blue-600 rounded-[2rem] font-black text-sm hover:bg-blue-500 disabled:opacity-20 transition-all shadow-[0_25px_50px_-12px_rgba(37,99,235,0.5)] flex items-center justify-center gap-3 group">
              Confirm Trip & Route
              <ArrowRight size={20} className="group-hover:translate-x-2 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, ArrowRight, Zap, Settings, Footprints, Train, 
  Smartphone, Car, BusFront, Sparkles, Navigation, ShieldCheck, 
  Search, ExternalLink, Loader2, Check, Banknote, Info, X, 
  ChevronUp, ChevronDown, AlertCircle, AlertTriangle, Moon, Plane, Clock
} from 'lucide-react';
import PageTransition from '../../components/PageTransition';
import { fetchWithAuth } from '../../authService'; 
import { API_BASE_URL } from '../../config';

// --- SUB-COMPONENT: Strategy Grid Item ---
const StrategyCard = ({ id, title, icon: Icon, isActive, disabled, onToggle, onSearchOffers, isSearching, description, hasOffers }) => (
  <div 
    onClick={() => !disabled && onToggle(id)}
    className={`relative p-5 rounded-[2rem] border-2 transition-all cursor-pointer flex flex-col gap-2 h-full ${
      isActive 
        ? 'border-blue-600 bg-blue-50/40 shadow-md translate-y-[-1px]' 
        : disabled 
          ? 'border-gray-100 bg-gray-50 opacity-30 cursor-not-allowed' 
          : 'border-gray-200 bg-white hover:border-blue-200 shadow-sm'
    }`}
  >
    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isActive ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500'}`}>
      <Icon size={20} />
    </div>
    <div className="flex-1 mt-1">
      <h4 className="font-black text-gray-900 text-[11px] uppercase tracking-tight">{title}</h4>
      <p className="text-[9px] text-gray-400 font-bold leading-tight mt-0.5">{description}</p>
    </div>
    {isActive && (id === 'public_transport' || id === 'rental_car') && (
      <button 
        onClick={(e) => { e.stopPropagation(); onSearchOffers(id); }}
        disabled={isSearching}
        className={`mt-auto w-full py-2 px-1 rounded-xl text-[9px] font-black uppercase tracking-tighter flex items-center justify-center gap-1.5 transition-all shadow-sm border ${
          hasOffers ? 'bg-green-600 border-green-600 text-white' : 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {isSearching ? <Loader2 size={12} className="animate-spin" /> : hasOffers ? <Check size={12} strokeWidth={3}/> : <Search size={12} strokeWidth={3}/>}
        <span className="truncate">{hasOffers ? "Details Found" : "Official Info"}</span>
      </button>
    )}
    {isActive && <div className="absolute top-3 right-3 bg-blue-600 text-white p-0.5 rounded-full shadow-sm border border-white"><Check size={10} strokeWidth={4} /></div>}
  </div>
);

export default function LogisticsStage({ gameState, session, refresh, onBack, onNext }) {
  const [prefMode, setPrefMode] = useState(gameState.mobility_config?.preference_mode || 'smart_optimization');
  const [strategies, setStrategies] = useState(gameState.mobility_config?.strategies || {});
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchingId, setSearchingId] = useState(null);
  const [activeOffer, setActiveOffer] = useState(null);

  const isDistanceTriggerOn = strategies.taxi_uber?.min_dist_km < 10000;

  useEffect(() => {
    if (gameState.mobility_config?.strategies) {
      setStrategies(gameState.mobility_config.strategies);
      setPrefMode(gameState.mobility_config.preference_mode);
    }
  }, [gameState]);

  const syncWithBackend = async (updatedMode, updatedStrategies) => {
    setIsSyncing(true);
    try {
      await fetchWithAuth(`${API_BASE_URL}/itinerary/update-mobility`, {
        session_id: session.id,
        config: { preference_mode: updatedMode, strategies: updatedStrategies }
      }, "POST");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSearchOffers = async (id) => {
    const actionMap = {
      'public_transport': 'search_public_transport_offers',
      'rental_car': 'search_rental_car_offers'
    };

    const action = actionMap[id];
    if (!action) return;

    setSearchingId(id);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/logistics/transport`, { 
        session_id: session.id, 
        action: action 
      }, "POST");

      if (res && res.ok) {
        const data = await res.json();
        const stratData = data.mobility_config.strategies[id];
        
        setActiveOffer({
          type: id,
          title: id === 'public_transport' ? "Public Transport Pass" : "Car Rental Estimate",
          price: id === 'public_transport' ? stratData.pass_price_est : stratData.daily_price_est,
          currency: stratData.currency || "EUR",
          link: stratData.official_link,
          hours: stratData.operating_hours,
          ztl: stratData.ztl_warning,
          location: gameState.search_location?.split(',')[0]
        });
        
        refresh();
      }
    } catch (err) { 
      console.error("Discovery error:", err); 
    } finally { 
      setSearchingId(null); 
    }
  };

  const toggleStrategy = (id) => {
    const newStrats = { ...strategies };
    const becomingEnabled = !newStrats[id].enabled;
    if (id === 'rental_car' && becomingEnabled) {
      Object.keys(newStrats).forEach(k => { if(k !== 'walking' && k !== 'rental_car') newStrats[k].enabled = false; });
      newStrats.rental_car.enabled = true;
    } else {
      newStrats[id].enabled = becomingEnabled;
      if (becomingEnabled && (id !== 'walking' && id !== 'rental_car')) newStrats.rental_car.enabled = false;
    }
    setStrategies(newStrats);
    syncWithBackend(prefMode, newStrats);
  };

  const updateVal = (id, field, val) => {
    const newStrats = { ...strategies, [id]: { ...strategies[id], [field]: val } };
    setStrategies(newStrats);
    syncWithBackend(prefMode, newStrats);
  };

  const movePriority = (id, direction) => {
    const enabledStrats = Object.entries(strategies)
      .filter(([_, s]) => s.enabled)
      .sort((a, b) => a[1].priority - b[1].priority);
    const currentIndex = enabledStrats.findIndex(([stratId]) => stratId === id);
    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= enabledStrats.length) return;

    const newOrder = [...enabledStrats];
    const [movedItem] = newOrder.splice(currentIndex, 1);
    newOrder.splice(newIndex, 0, movedItem);

    const updatedStrategies = { ...strategies };
    newOrder.forEach(([stratId], idx) => { updatedStrategies[stratId].priority = idx + 1; });
    setStrategies(updatedStrategies);
    syncWithBackend(prefMode, updatedStrategies);
  };

  // --- POPUP COMPONENT ---
  const renderOfferPopup = () => {
    if (!activeOffer) return null;
    const isRental = activeOffer.type === 'rental_car';

    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-gray-900/60 backdrop-blur-sm animate-fadeIn">
        <div className="bg-white w-full max-w-md rounded-[2.5rem] p-8 shadow-2xl relative animate-zoomIn">
          <button 
            onClick={() => setActiveOffer(null)} 
            className="absolute top-6 right-6 p-2 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-500 transition-colors"
          >
            <X size={18} />
          </button>
          
          <div className={`w-16 h-16 rounded-[1.5rem] flex items-center justify-center text-white mb-6 shadow-xl ${isRental ? 'bg-green-600 shadow-green-200' : 'bg-blue-600 shadow-blue-200'}`}>
            {isRental ? <Car size={32} /> : <Train size={32} />}
          </div>
          
          <h4 className={`text-[10px] font-black uppercase tracking-widest mb-2 ${isRental ? 'text-green-600' : 'text-blue-600'}`}>
            AI Logistics Discovery
          </h4>
          <h2 className="text-2xl font-black text-gray-900 leading-tight mb-4">{activeOffer.title} in {activeOffer.location}</h2>
          
          {isRental && activeOffer.ztl && (
            <div className="mb-4 bg-orange-50 border border-orange-100 p-4 rounded-2xl flex items-start gap-3">
              <AlertTriangle size={18} className="text-orange-600 shrink-0 mt-0.5" />
              <p className="text-[10px] font-bold text-orange-800 leading-tight">
                ZTL WARNING: Restricted traffic zones detected. Be careful with center driving and parking fines.
              </p>
            </div>
          )}

          <div className="bg-gray-50 rounded-3xl p-6 mb-6 flex items-center justify-between border border-gray-100">
             <div>
                <p className="text-[10px] font-black text-gray-400 uppercase mb-1">
                    {isRental ? "Estimated Daily Price" : "Estimated Full-Trip Price"}
                </p>
                <p className="text-3xl font-black text-gray-900">
                    {activeOffer.currency === 'EUR' ? '€' : activeOffer.currency}{activeOffer.price || '--'}
                </p>
             </div>
             <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-green-500 shadow-sm border border-gray-100">
                <Banknote size={24} />
             </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="bg-gray-50/50 border border-gray-100 rounded-2xl p-4 flex items-center gap-3">
              <Clock size={16} className="text-gray-400" />
              <div>
                <p className="text-[8px] font-black text-gray-400 uppercase tracking-tighter">Starts</p>
                <p className="text-xs font-black text-gray-900">{activeOffer.hours?.open || '08:00'}</p>
              </div>
            </div>
            <div className="bg-gray-50/50 border border-gray-100 rounded-2xl p-4 flex items-center gap-3">
              <Moon size={16} className="text-gray-400" />
              <div>
                <p className="text-[8px] font-black text-gray-400 uppercase tracking-tighter">Ends</p>
                <p className="text-xs font-black text-gray-900">{activeOffer.hours?.close || '22:00'}</p>
              </div>
            </div>
          </div>

          <p className="text-xs text-gray-500 leading-relaxed mb-8 italic">
            Data extracted from official sources for your specific trip dates. Prices include estimated 2026 inflation adjustments where applicable.
          </p>

          <a 
            href={activeOffer.link} 
            target="_blank" 
            rel="noopener noreferrer"
            className={`w-full text-white py-4 rounded-2xl font-black text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${isRental ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-900 hover:bg-blue-600'}`}
          >
            Visit Official Website <ExternalLink size={18} />
          </a>
        </div>
      </div>
    );
  };

  return (
    <PageTransition className="w-full h-full bg-gray-50 overflow-hidden flex flex-col p-8 relative">
      {renderOfferPopup()}
      
      <div className="max-w-7xl mx-auto w-full flex flex-col gap-8 h-full">
        
        {/* HEADER */}
        <div className="bg-white px-8 py-4 rounded-[2.5rem] border border-gray-100 shadow-sm flex items-center justify-between shrink-0">
          <button 
            onClick={onBack}
            className="flex items-center gap-2 text-gray-400 hover:text-blue-600 font-black text-xs uppercase tracking-widest transition-colors"
          >
            <ArrowLeft size={16} /> Back to attractions
          </button>
          <div className="flex items-center gap-4">
             {isSyncing && <div className="flex items-center gap-2 text-[10px] font-black text-blue-500 uppercase animate-pulse"><Loader2 size={14} className="animate-spin"/> Syncing Rules...</div>}
             <button className="bg-gray-900 text-white px-8 py-3 rounded-2xl font-black text-xs flex items-center gap-2 hover:bg-blue-600 shadow-lg active:scale-95 transition-all">
               Generate Schedule <ArrowRight size={16} />
             </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1 overflow-hidden">
          <div className="lg:col-span-2 flex flex-col gap-6 overflow-y-auto pr-4 custom-scrollbar pb-32">
            
            {/* OPTIMIZATION MODES */}
            <div className="bg-white rounded-[3.5rem] p-10 border border-gray-200 shadow-sm">
              <div className="flex flex-col md:flex-row justify-between items-start mb-10 gap-8">
                <div className="flex-1">
                  <h3 className="text-3xl font-black text-gray-900 tracking-tight">Mobility Optimization</h3>
                  <p className="text-gray-500 text-sm font-medium mt-2">Pick your active modes and choose your control level.</p>
                </div>

                <div className="flex flex-col gap-3 w-full md:w-[400px] shrink-0">
                  {['smart_optimization', 'manual_rules'].map(m => (
                    <div key={m} onClick={() => { setPrefMode(m); syncWithBackend(m, strategies); }} className={`p-4 rounded-2xl border-2 transition-all cursor-pointer ${prefMode === m ? 'bg-blue-50 border-blue-600' : 'bg-gray-50 border-transparent opacity-50'}`}>
                      <div className="flex items-center gap-2 font-black text-[10px] text-blue-700 uppercase mb-1">
                        {m === 'smart_optimization' ? <Zap size={14}/> : <Settings size={14}/>} 
                        {m === 'smart_optimization' ? 'Automatic (Smart)' : 'Manual (Strict)'}
                        {prefMode === m && <Check size={14} className="ml-auto" />}
                      </div>
                      <p className="text-[10px] text-gray-600 leading-relaxed font-medium">
                        {m === 'smart_optimization' ? 'AI optimizes for cost and time efficiency automatically.' : 'The system follows your hierarchy and manual thresholds.'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-10">
                <StrategyCard 
                    id="walking" title="Walk" icon={Footprints} 
                    isActive={strategies.walking?.enabled} onToggle={toggleStrategy} description="Max 15m" 
                />
                <StrategyCard 
                    id="public_transport" title="Transit" icon={Train} 
                    isActive={strategies.public_transport?.enabled} disabled={strategies.rental_car?.enabled} 
                    onToggle={toggleStrategy} onSearchOffers={handleSearchOffers} isSearching={searchingId === 'public_transport'}
                    hasOffers={!!strategies.public_transport?.details_loaded} description="Metro/Bus" 
                />
                <StrategyCard 
                    id="taxi_uber" title="Ride" icon={Smartphone} 
                    isActive={strategies.taxi_uber?.enabled} disabled={strategies.rental_car?.enabled} onToggle={toggleStrategy} description="Uber/Taxi" 
                />
                <StrategyCard 
                    id="rental_car" 
                    title="Rental" 
                    icon={Car} 
                    isActive={strategies.rental_car?.enabled} 
                    onToggle={toggleStrategy} 
                    onSearchOffers={handleSearchOffers} 
                    isSearching={searchingId === 'rental_car'}
                    hasOffers={!!strategies.rental_car?.details_loaded} 
                    description="Car Hire" 
                />
                <StrategyCard 
                    id="intercity" title="Day Trips" icon={BusFront} 
                    isActive={strategies.intercity?.enabled} disabled={strategies.rental_car?.enabled} onToggle={toggleStrategy} description="Inter-City" 
                />
              </div>

              {/* PRIORITY STACK */}
              <div className="bg-gray-50 rounded-[2.5rem] p-8 border border-gray-100">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-2">
                  <h4 className="font-black text-sm uppercase tracking-widest text-gray-900 flex items-center gap-2"><Navigation size={18} className="text-blue-600"/> Decision Hierarchy</h4>
                  <span className="text-[10px] font-bold text-blue-500 bg-blue-100/50 px-3 py-1 rounded-full border border-blue-100 italic">
                    * Stick with defaults for best experience.
                  </span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(strategies)
                    .filter(([_, s]) => s.enabled)
                    .sort((a, b) => a[1].priority - b[1].priority)
                    .map(([id, s], idx, arr) => (
                      <div key={id} className="bg-white border border-gray-200 p-4 rounded-2xl flex items-center gap-4 shadow-sm group">
                        <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-black text-xs flex items-center justify-center">#{idx + 1}</div>
                        <div className="flex-1 font-black text-xs uppercase text-gray-700">{id.replace('_', ' ')}</div>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                           <button onClick={() => movePriority(id, 'up')} disabled={idx === 0} className="p-1.5 hover:bg-gray-100 rounded-lg disabled:opacity-10"><ChevronUp size={16}/></button>
                           <button onClick={() => movePriority(id, 'down')} disabled={idx === arr.length - 1} className="p-1.5 hover:bg-gray-100 rounded-lg disabled:opacity-10"><ChevronDown size={16}/></button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            {/* MANUAL CONSTRAINTS */}
            {prefMode === 'manual_rules' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {strategies.walking?.enabled && (
                  <div className="bg-white p-8 rounded-[3rem] border border-gray-200 shadow-sm">
                    <h4 className="font-black text-[10px] uppercase tracking-widest text-blue-600 mb-6 flex items-center gap-2"><Footprints size={14}/> Walking Constraint</h4>
                    <div className="flex justify-between mb-4"><span className="text-xs font-bold text-gray-500">Maximum Duration</span><span className="font-black text-xl">{strategies.walking.max_time_mins}m</span></div>
                    <input type="range" min="5" max="45" step="5" value={strategies.walking.max_time_mins} onChange={(e) => updateVal('walking', 'max_time_mins', parseInt(e.target.value))} className="w-full h-2 bg-gray-100 rounded-lg appearance-none accent-blue-600 cursor-pointer" />
                  </div>
                )}
                {strategies.taxi_uber?.enabled && (
                  <div className="bg-white p-8 rounded-[3rem] border border-gray-200 shadow-sm">
                    <h4 className="font-black text-[10px] uppercase tracking-widest text-blue-600 mb-6 flex items-center gap-2"><Smartphone size={14}/> Taxi Fallbacks</h4>
                    <div className="space-y-3">
                       <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl cursor-pointer">
                          <input type="checkbox" checked={strategies.taxi_uber.trigger_late_night} onChange={(e) => updateVal('taxi_uber', 'trigger_late_night', e.target.checked)} className="w-5 h-5 accent-blue-600" />
                          <div className="flex items-center gap-2 text-[11px] font-bold"><Moon size={14}/> Late Night</div>
                       </label>
                       <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl cursor-pointer">
                          <input type="checkbox" checked={strategies.taxi_uber.trigger_airport_transfer} onChange={(e) => updateVal('taxi_uber', 'trigger_airport_transfer', e.target.checked)} className="w-5 h-5 accent-blue-600" />
                          <div className="flex items-center gap-2 text-[11px] font-bold"><Plane size={14}/> Airport Legs</div>
                       </label>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* SIDEBAR */}
          <div className="bg-gray-900 rounded-[3rem] p-10 text-white flex flex-col h-full shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-48 h-48 bg-blue-600/20 rounded-full -mr-24 -mt-24 blur-3xl" />
            <h3 className="font-black text-2xl flex items-center gap-3 relative z-10"><Sparkles className="text-blue-400" /> Logistics Insights</h3>
            <div className="mt-10 space-y-6 relative z-10 flex-1 overflow-y-auto pr-2 custom-scrollbar">
               {strategies.rental_car?.enabled && (
                 <div className="bg-orange-500/10 border border-orange-500/30 p-6 rounded-3xl border-l-4 border-l-orange-500 animate-in slide-in-from-right">
                    <div className="flex items-center gap-3 mb-3 text-orange-400 font-black text-xs uppercase"><AlertTriangle size={16}/> Traffic Area Warning</div>
                    <p className="text-[11px] text-gray-400 leading-relaxed">Central areas often have ZTL zones. Fines apply without permits.</p>
                 </div>
               )}
            </div>
            <div className="mt-auto pt-8 border-t border-white/10 text-center relative z-10 text-[10px] font-black text-gray-500 uppercase tracking-widest">
               thread_itinerary_{session.id}
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
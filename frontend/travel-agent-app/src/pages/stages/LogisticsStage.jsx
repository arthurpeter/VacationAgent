import React, { useEffect, useMemo, useState, useRef } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Car,
  Train,
  AlertTriangle,
  Check,
  Loader2,
  ExternalLink,
  Clock,
  Banknote,
  Activity
} from 'lucide-react';

import PageTransition from '../../components/PageTransition';
import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';

// ----------------------------------------------------------------------
// SUB-COMPONENTS
// ----------------------------------------------------------------------

function SectionHeader({ title, subtitle }) {
    return (
        <div className="mb-4">
            <h2 className="text-2xl font-black text-gray-900">{title}</h2>
            {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
    );
}

function AIRecommendationCard({ title, recommendation, reasoning, icon: Icon, colorClass }) {
    return (
        <div className={`bg-white p-5 rounded-xl border-l-4 ${colorClass} shadow-sm flex gap-4 items-start h-full`}>
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${colorClass.replace('border-', 'bg-').replace('500', '100')} ${colorClass.replace('border-', 'text-')}`}>
                <Icon size={20} />
            </div>
            <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-1">
                    AI Recommended {title}
                </p>
                <h3 className="text-lg font-black text-gray-900 leading-tight">
                    {recommendation}
                </h3>
                <p className="text-xs text-gray-500 mt-2 leading-relaxed">
                    {reasoning}
                </p>
            </div>
        </div>
    );
}

function TransportCard({ active, onClick, title, description, icon: Icon, detailsLoaded }) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`relative text-left p-5 rounded-xl border-2 transition group flex flex-col h-full ${
                active
                    ? 'border-blue-500 bg-blue-50/50 shadow-md ring-2 ring-blue-100'
                    : 'border-transparent bg-white shadow-sm hover:shadow-md'
            }`}
        >
            {active && (
                <div className="absolute top-4 right-4 w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-sm">
                    <Check size={12} strokeWidth={4} />
                </div>
            )}

            {detailsLoaded && (
                <div className="absolute top-4 left-4 flex items-center gap-1 text-[9px] uppercase tracking-wider font-bold text-green-600 bg-green-100 px-2 py-1 rounded-md">
                    <Check size={10} strokeWidth={4} />
                    Fetched
                </div>
            )}
            
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-colors ${detailsLoaded ? 'mt-4' : ''} ${
                active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500 group-hover:bg-gray-200'
            }`}>
                <Icon size={24} />
            </div>

            <h3 className="text-lg font-black text-gray-900(BC1)">{title}</h3>
            <p className="mt-1 text-xs text-gray-500 leading-relaxed flex-grow">
                {description}
            </p>
        </button>
    );
}

function PaceSlider({ value, onChange }) {
    const options = [
        { id: 'relaxed', label: 'Relaxed', hours: '2-4 hours/day' },
        { id: 'moderate', label: 'Moderate', hours: '5-7 hours/day' },
        { id: 'fast', label: 'Fast-Paced', hours: '8+ hours/day' }
    ];

    const getTranslateX = () => {
        if (value === 'relaxed') return 'translate-x-0';
        if (value === 'moderate') return 'translate-x-full';
        return 'translate-x-[200%]';
    };

    return (
        <div className="relative flex bg-gray-100 rounded-xl p-1.5 w-full">
            <div 
                className={`absolute top-1.5 bottom-1.5 w-[calc(33.333%-4px)] bg-white rounded-lg shadow-sm transition-transform duration-300 ease-in-out z-0 ${getTranslateX()}`}
            />
            {options.map((opt) => (
                <button
                    type="button"
                    key={opt.id}
                    onClick={() => onChange(opt.id)}
                    className={`flex-1 py-4 text-center rounded-lg z-10 transition-colors duration-300 ${
                        value === opt.id ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'
                    }`}
                >
                    <div className="text-sm font-black">{opt.label}</div>
                    <div className={`text-[10px] font-bold uppercase tracking-wider mt-1 ${value === opt.id ? 'text-blue-600' : 'text-gray-400'}`}>
                        {opt.hours}
                    </div>
                </button>
            ))}
        </div>
    );
}

// ----------------------------------------------------------------------
// MAIN STAGE COMPONENT
// ----------------------------------------------------------------------

export default function LogisticsStage({ gameState, session, refresh, onBack, onNext }) {
  const [selectedTransport, setSelectedTransport] = useState(() => {
    if (gameState?.mobility_config?.strategies?.rental_car?.enabled) return 'rental_car';
    return 'public_transport';
  });
  
  const [selectedPace, setSelectedPace] = useState(gameState?.pace || 'moderate');
  
  const [loadingRecommendations, setLoadingRecommendations] = useState(true);
  const [loadingTransportInfo, setLoadingTransportInfo] = useState(false);

  const hasTriggeredAI = useRef(false);

  const mobilityRecommendation = gameState?.mobility_recommendation;
  const paceRecommendation = gameState?.pace_recommendation;

  const hasMobility = !!mobilityRecommendation;
  const hasPace = !!paceRecommendation;

  const activeStrategyData = gameState?.mobility_config?.strategies?.[selectedTransport];
  const isDetailsLoaded = activeStrategyData?.details_loaded;

  // 1. Trigger AI and Poll State
  useEffect(() => {
    let pollInterval;
    let isMounted = true;

    const checkAndFetch = async () => {
        if (hasMobility && hasPace) {
            setLoadingRecommendations(false);
            return;
        }

        setLoadingRecommendations(true);

        if (!hasTriggeredAI.current) {
            hasTriggeredAI.current = true;
            try {
                if (!hasMobility) {
                    await fetchWithAuth(`${API_BASE_URL}/itinerary/logistics/transport`, {
                        session_id: session.id, action: 'mobility_recommendation'
                    }, 'POST');
                }
                if (!hasPace) {
                    await fetchWithAuth(`${API_BASE_URL}/itinerary/logistics/transport`, {
                        session_id: session.id, action: 'pace_recommendation'
                    }, 'POST');
                }
            } catch (e) {
                console.error("Failed to trigger AI Graph:", e);
            }
        }

        pollInterval = setInterval(() => {
            if (isMounted && refresh) refresh();
        }, 2000);
    };

    checkAndFetch();

    return () => {
        isMounted = false;
        if (pollInterval) clearInterval(pollInterval);
    };
  }, [hasMobility, hasPace, refresh, session.id]);


  // Recommendations formatting
  const recommendedTransport = useMemo(() => {
    if (!mobilityRecommendation) return null;
    return mobilityRecommendation.should_rent_car ? 'rental_car' : 'public_transport';
  }, [mobilityRecommendation]);

  const recommendedPace = useMemo(() => {
    if (!paceRecommendation?.recommended_pace) return null;
    const rec = paceRecommendation.recommended_pace.toLowerCase();
    if (rec.includes('relax')) return 'relaxed';
    if (rec.includes('fast') || rec.includes('pack')) return 'fast';
    return 'moderate';
  }, [paceRecommendation]);

  const isTransportAgainst = recommendedTransport && selectedTransport !== recommendedTransport;
  const isPaceAgainst = recommendedPace && selectedPace !== recommendedPace;

  // 2. Network Handlers
  const handleTransportSelect = async (type) => {
    setSelectedTransport(type);
    
    const existingConfig = gameState?.mobility_config || {};
    const existingStrategies = existingConfig.strategies || {};

    const updatedConfig = {
        ...existingConfig,
        preference_mode: 'smart_optimization',
        strategies: {
            ...existingStrategies,
            public_transport: {
                ...(existingStrategies.public_transport || {}),
                enabled: type === 'public_transport'
            },
            rental_car: {
                ...(existingStrategies.rental_car || {}),
                enabled: type === 'rental_car'
            }
        }
    };

    try {
        await fetchWithAuth(`${API_BASE_URL}/itinerary/update-mobility`, {
            session_id: session.id,
            config: updatedConfig,
        }, 'POST');
        refresh();
    } catch (e) {
        console.error(e);
    }
  };

  const handlePaceSelect = async (newPace) => {
    setSelectedPace(newPace);
    try {
        await fetchWithAuth(`${API_BASE_URL}/itinerary/logistics/pace`, {
            session_id: session.id,
            pace: newPace,
        }, 'POST');
        refresh();
    } catch (e) {
        console.error(e);
    }
  };

  const handleFetchDetails = async () => {
    setLoadingTransportInfo(true);
    try {
      const action = selectedTransport === 'rental_car' ? 'search_rental_car_offers' : 'search_public_transport_offers';
      await fetchWithAuth(`${API_BASE_URL}/itinerary/logistics/transport`, {
          session_id: session.id,
          action,
      }, 'POST');
      refresh();
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingTransportInfo(false);
    }
  };

  const handleContinue = async () => {
    try {
        await fetchWithAuth(`${API_BASE_URL}/itinerary/logistics/pace`, {
            session_id: session.id,
            pace: selectedPace,
        }, 'POST');
        onNext();
    } catch (e) {
        console.error(e);
    }
  };

  return (
    <PageTransition className="flex flex-col w-full h-full bg-gray-50 overflow-hidden relative">
      
      {/* FLOATING ACTION OVERLAY CONTROLS */}
      {/* Floating Back Button (Glows Red on Hover) */}
      <div className="absolute top-3 left-8 z-[100] pointer-events-auto">
        <button 
          type="button"
          onClick={onBack} 
          className="px-4 py-3 bg-transparent text-gray-400 hover:text-red-500 rounded-2xl font-black text-xs uppercase tracking-wider flex items-center gap-2 transition-all duration-300 group"
        >
          <ArrowLeft size={14} className="transform transition-transform group-hover:-translate-x-1" />
          <span>Back</span>
        </button>
      </div>

      {/* Floating Forward Button (Glows Blue on Hover) */}
      <div className="absolute top-3 right-8 z-[100] pointer-events-auto">
        <button 
          type="button"
          onClick={handleContinue} 
          disabled={loadingRecommendations}
          className="px-4 py-3 bg-transparent text-gray-400 hover:text-blue-500 rounded-2xl font-black text-xs uppercase tracking-wider flex items-center gap-2 transition-all duration-300 group disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <span>Generate Itinerary</span>
          <ArrowRight size={14} className="transform transition-transform group-hover:translate-x-1" />
        </button>
      </div>

      {/* IMMERSIVE MAIN LAYOUT SCROLL CONTAINER */}
      <div className="flex-grow overflow-y-auto p-8 pt-16 z-10">
        <div className="max-w-4xl mx-auto space-y-8">
            
            <div>
                <h1 className="text-4xl font-black text-gray-900 tracking-tight">Logistics & Pace</h1>
                <p className="text-gray-500 mt-2 font-medium">Fine-tune the dynamics of your daily schedule.</p>
            </div>

            <section className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                <SectionHeader 
                    title="AI Trip Intelligence" 
                    subtitle="Based on your destination, group size, and dates, here is what we recommend." 
                />
                
                {loadingRecommendations ? (
                    <div className="bg-blue-50 rounded-xl p-8 border border-blue-100 flex flex-col items-center justify-center gap-3">
                        <Loader2 className="animate-spin text-blue-600" size={28} />
                        <span className="font-bold text-blue-800 text-sm uppercase tracking-widest">
                            AI is analyzing optimal routes...
                        </span>
                        <p className="text-xs text-blue-600">This might take a few seconds.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        {mobilityRecommendation && (
                            <AIRecommendationCard
                                title="Mobility"
                                recommendation={mobilityRecommendation.recommendation}
                                reasoning={mobilityRecommendation.reasoning}
                                icon={recommendedTransport === 'rental_car' ? Car : Train}
                                colorClass="border-blue-500 text-blue-600"
                            />
                        )}
                        {paceRecommendation && (
                            <AIRecommendationCard
                                title="Pace"
                                recommendation={paceRecommendation.recommendation}
                                reasoning={paceRecommendation.reasoning}
                                icon={Activity}
                                colorClass="border-purple-500 text-purple-600"
                            />
                        )}
                    </div>
                )}
            </section>

            {/* Custom Warning Banners Section */}
            {!loadingRecommendations && (isTransportAgainst || isPaceAgainst) && (
                <div className="space-y-4">
                    {isTransportAgainst && (
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex items-start gap-4 shadow-sm animate-in fade-in slide-in-from-top-2">
                            <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center shrink-0">
                                <AlertTriangle size={20} />
                            </div>
                            <div>
                                <h3 className="font-black text-amber-800 text-sm uppercase tracking-wider mb-1">
                                    Transport Override
                                </h3>
                                <p className="text-sm text-amber-700 leading-relaxed">
                                    Our AI recommended <strong>{recommendedTransport === 'rental_car' ? 'Renting a Car' : 'Public Transit'}</strong>, but you've opted for <strong>{selectedTransport === 'rental_car' ? 'a Rental Car' : 'Public Transit'}</strong>. Don't worry—your routes and estimates will be tailored to your choice!
                                </p>
                            </div>
                        </div>
                    )}
                    
                    {isPaceAgainst && (
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 flex items-start gap-4 shadow-sm animate-in fade-in slide-in-from-top-2">
                            <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center shrink-0">
                                <AlertTriangle size={20} />
                            </div>
                            <div>
                                <h3 className="font-black text-amber-800 text-sm uppercase tracking-wider mb-1">
                                    Custom Pace Selected
                                </h3>
                                <p className="text-sm text-amber-700 leading-relaxed">
                                    Our AI suggested a <strong>{recommendedPace}</strong> schedule, but you've chosen a <strong>{selectedPace}</strong> pace. The density of your daily activities will be customized to match your preferred speed!
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                <section>
                    <SectionHeader 
                        title="Vacation Pace" 
                        subtitle="How much time per day will you spend visiting attractions?" 
                    />
                    <div className="mt-4">
                        <PaceSlider value={selectedPace} onChange={handlePaceSelect} />
                    </div>
                </section>

                <section>
                    <SectionHeader 
                        title="Getting Around" 
                        subtitle="Choose your preferred transportation style." 
                    />
                    <div className="grid grid-cols-2 gap-4 mt-4">
                        <TransportCard
                            active={selectedTransport === 'public_transport'}
                            onClick={() => handleTransportSelect('public_transport')}
                            title="Transit"
                            description="Best for city centers and museums."
                            icon={Train}
                            detailsLoaded={gameState?.mobility_config?.strategies?.public_transport?.details_loaded}
                        />
                        <TransportCard
                            active={selectedTransport === 'rental_car'}
                            onClick={() => handleTransportSelect('rental_car')}
                            title="Rental Car"
                            description="Best for remote sites and nature."
                            icon={Car}
                            detailsLoaded={gameState?.mobility_config?.strategies?.rental_car?.details_loaded}
                        />
                    </div>
                </section>
            </div>

            <div className="mt-2">
                {!isDetailsLoaded ? (
                    <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6 flex flex-col items-center justify-center text-center animate-in fade-in duration-300">
                        <p className="text-sm text-blue-800 font-medium mb-4">
                            Would you like to fetch real-time estimates and official resources for {selectedTransport === 'rental_car' ? 'rental cars' : 'public transit'}?
                        </p>
                        <button 
                            type="button"
                            onClick={handleFetchDetails}
                            disabled={loadingTransportInfo}
                            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-6 rounded-xl transition-all flex items-center gap-2 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loadingTransportInfo ? (
                                <><Loader2 size={18} className="animate-spin" /> Fetching Official Data...</>
                            ) : (
                                <><Banknote size={18} /> Get Official Prices & Info</>
                            )}
                        </button>
                    </div>
                ) : (
                    <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm animate-in fade-in zoom-in-95 duration-300">
                        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-100 pb-4 mb-4">
                            <div>
                                <p className="text-[10px] uppercase tracking-widest font-black text-gray-400">
                                    Official Logistics
                                </p>
                                <h3 className="text-xl font-black text-gray-900 mt-1">
                                    {selectedTransport === 'rental_car' ? 'Rental Car Estimate' : 'Transit Pass Info'}
                                </h3>
                            </div>
                            
                            <div className="bg-gray-50 rounded-xl border border-gray-200 px-4 py-2 flex items-center gap-3">
                                <Banknote className="text-green-600" size={20} />
                                <div>
                                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Est. Price</p>
                                    <p className="text-lg font-black text-gray-900 leading-none mt-0.5">
                                        {activeStrategyData.currency || 'EUR'} {activeStrategyData.daily_price_est || activeStrategyData.pass_price_est}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {activeStrategyData.ztl_warning && (
                            <div className="mb-4 bg-orange-50 border border-orange-100 rounded-lg p-3 flex items-center gap-3 text-sm text-orange-800">
                                <AlertTriangle size={16} className="text-orange-500 shrink-0" />
                                <span className="font-medium">Restricted traffic zones (ZTL) are active in this destination. Plan your parking carefully.</span>
                            </div>
                        )}

                        <div className="flex items-center gap-6 flex-wrap text-sm">
                            <div className="flex items-center gap-2 text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-100">
                                <Clock size={16} className="text-gray-400" />
                                <span className="font-bold">
                                    Active: {activeStrategyData.operating_hours?.open || '05:00'} - {activeStrategyData.operating_hours?.close || '23:00'}
                                </span>
                            </div>

                            {activeStrategyData.official_link && (
                                <a
                                    href={activeStrategyData.official_link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 font-bold transition-colors ml-auto"
                                >
                                    Visit Official Website
                                    <ExternalLink size={14} />
                                </a>
                            )}
                        </div>
                    </div>
                )}
            </div>

        </div>
      </div>
    </PageTransition>
  );
}
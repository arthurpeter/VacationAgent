import React, { useEffect, useState, useRef } from 'react';
import {
    ArrowLeft,
    ArrowRight,
    Loader2,
    MapPin,
    Coffee,
    Utensils,
    AlertTriangle,
    CalendarDays,
    Sparkles,
    TrainFront,
    Sun,
    RefreshCw
} from 'lucide-react';
import PageTransition from '../../components/PageTransition';
import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';
import ItineraryMap from '../../components/ItineraryMap';

// --- HELPER COMPONENTS ---

function EventCard({ event }) {
    const isMeal = event.type === 'meal';
    const isFreeTime = event.type === 'free_time';
    const isAttraction = event.type === 'attraction';

    let bgClass = "bg-white border-gray-200";
    let iconBg = "bg-gray-100 text-gray-500";
    let Icon = MapPin;

    if (isMeal) {
        bgClass = "bg-orange-50 border-orange-100";
        iconBg = "bg-orange-100 text-orange-600";
        Icon = Utensils;
    } else if (isFreeTime) {
        bgClass = "bg-blue-50 border-blue-100";
        iconBg = "bg-blue-100 text-blue-600";
        Icon = Coffee;
    } else if (isAttraction) {
        Icon = MapPin;
        if (event.bucket === 'must-see') {
            iconBg = "bg-purple-100 text-purple-600";
            bgClass = "bg-white border-purple-100 shadow-sm";
        } else {
            iconBg = "bg-blue-100 text-blue-600";
        }
    }

    return (
        <div className="relative flex flex-col gap-2 group">
            {event.transit_mins > 0 && (
                <div className="flex items-center gap-2 ml-4 text-xs font-bold text-gray-400 uppercase tracking-widest my-1">
                    <TrainFront size={14} />
                    <span>~{event.transit_mins} min travel</span>
                </div>
            )}

            <div className={`p-4 rounded-xl border flex items-start gap-4 transition-all hover:shadow-md ${bgClass}`}>
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${iconBg}`}>
                    <Icon size={20} />
                </div>
                
                <div className="flex-grow">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs font-black uppercase tracking-wider text-gray-400 mb-0.5">
                                {event.start_time} - {event.end_time}
                            </p>
                            <h4 className={`text-lg font-black leading-tight ${isMeal || isFreeTime ? 'text-gray-700' : 'text-gray-900'}`}>
                                {event.name}
                            </h4>
                        </div>
                        
                        {isAttraction && event.bucket && (
                            <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded-md ${
                                event.bucket === 'must-see' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
                            }`}>
                                {event.bucket.replace('-', ' ')}
                            </span>
                        )}
                    </div>

                    {event.unknown_hours_warning && (
                        <div className="mt-3 bg-amber-50 rounded-lg p-2 flex items-center gap-2 text-xs text-amber-800 border border-amber-100">
                            <AlertTriangle size={14} className="text-amber-500 shrink-0" />
                            <span>We couldn't verify the opening hours for this location.</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// --- MAIN COMPONENT ---

export default function ScheduleStage({ gameState, session, refresh, onBack, onNext }) {
    const [isGenerating, setIsGenerating] = useState(false);
    
    const [localSchedule, setLocalSchedule] = useState(null);
    const [localExcluded, setLocalExcluded] = useState(null);
    
    const [activeMapDay, setActiveMapDay] = useState(0); 
    const hasTriggered = useRef(false);

    const schedule = gameState?.schedule || localSchedule;
    const excluded = gameState?.excluded_pois || localExcluded;
    
    // Extract base trip details from global state
    const baseTripDetails = gameState?.trip_details || {};

    // NEW: Local state for UI controls, initializing from existing state
    const [wakeupTime, setWakeupTime] = useState(baseTripDetails.wakeup_time || "08:00");
    const [lunchDuration, setLunchDuration] = useState(baseTripDetails.lunch_duration_mins || 90);

    useEffect(() => {
        if (!schedule && !hasTriggered.current) {
            hasTriggered.current = true;
            generateSchedule();
        }
    }, [schedule]);

    const generateSchedule = async () => {
        setIsGenerating(true);
        try {
            const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/schedule/action`, {
                session_id: session.id,
                action: "generate_schedule"
            }, "POST");
            
            if (res.ok) {
                const data = await res.json();
                if (data.schedule) setLocalSchedule(data.schedule);
                if (data.excluded_pois) setLocalExcluded(data.excluded_pois);
            }
            
            await refresh();
        } catch (e) {
            console.error("Failed to generate schedule", e);
        } finally {
            setIsGenerating(false);
        }
    };

    // NEW: Handle user clicking "Recalculate"
    const handleRecalculate = async () => {
        setIsGenerating(true);
        try {
            // 1. Merge the new parameters with the existing trip coordinates/dates
            const updatedDetails = {
                ...baseTripDetails,
                wakeup_time: wakeupTime,
                lunch_duration_mins: parseInt(lunchDuration, 10)
            };

            // 2. Save the new settings to the graph state
            await fetchWithAuth(`${API_BASE_URL}/itinerary/schedule/details`, {
                session_id: session.id,
                trip_details: updatedDetails
            }, "POST");

            // 3. Re-trigger the generation sequence using the new settings
            const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/schedule/action`, {
                session_id: session.id,
                action: "generate_schedule"
            }, "POST");
            
            if (res.ok) {
                const data = await res.json();
                if (data.schedule) setLocalSchedule(data.schedule);
                if (data.excluded_pois) setLocalExcluded(data.excluded_pois);
            }
            
            await refresh();
        } catch (e) {
            console.error("Recalculation failed", e);
        } finally {
            setIsGenerating(false);
        }
    };

    if (isGenerating || !schedule || schedule.length === 0) {
        return (
            <PageTransition className="flex flex-col items-center justify-center w-full h-full bg-gray-50">
                <div className="bg-white p-10 rounded-3xl shadow-lg border border-gray-100 flex flex-col items-center max-w-md text-center">
                    <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mb-6">
                        <Sparkles className="text-blue-600 animate-pulse" size={32} />
                    </div>
                    <h2 className="text-2xl font-black text-gray-900 mb-2">Building Your Timeline</h2>
                    <p className="text-sm text-gray-500 mb-8 leading-relaxed">
                        Our AI is mathematically calculating optimal routes, checking opening hours, and perfectly balancing your daily pace...
                    </p>
                    <Loader2 className="animate-spin text-blue-600" size={32} />
                </div>
            </PageTransition>
        );
    }

    return (
        <PageTransition className="flex flex-col w-full h-full bg-gray-50 overflow-hidden">
            {/* Top Navigation Bar */}
            <div className="bg-white border-b border-gray-200 p-4 shadow-sm shrink-0 flex items-center justify-between z-20">
                <button 
                    onClick={onBack} 
                    className="flex items-center gap-2 text-gray-500 hover:text-blue-600 font-bold px-4 py-2 rounded-lg hover:bg-blue-50 transition"
                >
                    <ArrowLeft size={18} />
                    Back
                </button>
                
                <button 
                    onClick={onNext}
                    className="px-6 py-2.5 bg-gray-900 hover:bg-black text-white rounded-lg font-bold shadow-md flex items-center gap-2 transition-transform hover:-translate-y-0.5"
                >
                    Finalize & View Map
                    <ArrowRight size={18} />
                </button>
            </div>

            {/* SPLIT SCREEN LAYOUT */}
            <div className="flex flex-row flex-grow overflow-hidden">
                
                {/* LEFT PANEL: Scrollable Timeline */}
                <div className="w-full lg:w-[45%] flex-grow overflow-y-auto p-8 z-10 bg-gray-50 relative">
                    <div className="max-w-xl mx-auto">
                        
                        <div className="mb-6">
                            <h1 className="text-4xl font-black text-gray-900 tracking-tight">Your Itinerary Draft</h1>
                            <p className="text-gray-500 mt-2 font-medium">Review your daily timeline. Adjust parameters to regenerate.</p>
                        </div>

                        {/* --- NEW: GLOBAL SETTINGS BAR --- */}
                        <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm mb-10 flex flex-col sm:flex-row items-center justify-between gap-4 sticky top-0 z-50">
                            <div className="flex items-center gap-6 w-full sm:w-auto">
                                
                                {/* Wakeup Time Control */}
                                <div className="flex flex-col gap-1">
                                    <label className="text-[10px] font-black uppercase tracking-wider text-gray-400 flex items-center gap-1">
                                        <Sun size={12} /> Start Time
                                    </label>
                                    <input 
                                        type="time" 
                                        value={wakeupTime}
                                        onChange={(e) => setWakeupTime(e.target.value)}
                                        className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-sm font-bold text-gray-900 outline-none focus:border-blue-500"
                                    />
                                </div>

                                {/* Lunch Duration Control */}
                                <div className="flex flex-col gap-1">
                                    <label className="text-[10px] font-black uppercase tracking-wider text-gray-400 flex items-center gap-1">
                                        <Utensils size={12} /> Lunch
                                    </label>
                                    <select 
                                        value={lunchDuration}
                                        onChange={(e) => setLunchDuration(e.target.value)}
                                        className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-sm font-bold text-gray-900 outline-none focus:border-blue-500 cursor-pointer"
                                    >
                                        <option value="45">45 Mins</option>
                                        <option value="60">1 Hour</option>
                                        <option value="90">1.5 Hours</option>
                                        <option value="120">2 Hours</option>
                                    </select>
                                </div>
                                
                            </div>

                            <button 
                                onClick={handleRecalculate}
                                className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2 rounded-xl flex items-center justify-center gap-2 shadow-sm transition-all active:scale-95"
                            >
                                <RefreshCw size={16} />
                                Recalculate
                            </button>
                        </div>
                        {/* --- END SETTINGS BAR --- */}

                        {/* The Timeline */}
                        <div className="space-y-12">
                            {schedule.map((day, idx) => {
                                const dateObj = new Date(day.date);
                                const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
                                const shortDate = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

                                return (
                                    <div key={idx} id={`timeline-day-${idx}`} className="relative">
                                        <div className="sticky top-[88px] z-10 bg-gray-50/90 backdrop-blur-md py-4 mb-4 border-b border-gray-200 flex items-center gap-3">
                                            <div className="bg-gray-900 text-white w-10 h-10 rounded-xl flex items-center justify-center font-black shadow-sm">
                                                {day.day_index + 1}
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-black text-gray-900">{dayName}</h3>
                                                <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">{shortDate}</p>
                                            </div>
                                        </div>

                                        <div className="pl-4 border-l-2 border-gray-200 ml-4 space-y-4 py-2">
                                            {day.events.map((evt, eIdx) => (
                                                <EventCard key={eIdx} event={evt} />
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Excluded Items Parking Lot */}
                        {(excluded?.['must-see']?.length > 0 || excluded?.['want-to-see']?.length > 0 || excluded?.['optional']?.length > 0) && (
                            <div className="mt-16 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                                <div className="flex items-center gap-3 mb-4 border-b border-gray-100 pb-4">
                                    <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-gray-500">
                                        <CalendarDays size={20} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-black text-gray-900">Dropped Attractions</h3>
                                        <p className="text-xs text-gray-500">These didn't fit the time limits or opening hours.</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {['must-see', 'want-to-see', 'optional'].map(bucket => {
                                        const items = excluded[bucket];
                                        if (!items || items.length === 0) return null;
                                        return (
                                            <div key={bucket} className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                                                <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">{bucket.replace('-', ' ')}</h4>
                                                <ul className="space-y-2">
                                                    {items.map((name, i) => (
                                                        <li key={i} className="text-xs font-medium text-gray-700 bg-white px-3 py-2 rounded-lg border border-gray-200 shadow-sm">
                                                            {name}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                    </div>
                </div>

                {/* RIGHT PANEL: Tabbed Map Container */}
                <div className="hidden lg:flex flex-col lg:w-[55%] relative bg-gray-200 border-l border-gray-200 shadow-inner z-0">
                    
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/90 backdrop-blur-md p-1.5 rounded-full shadow-lg border border-gray-200 flex gap-1 overflow-x-auto max-w-[90%]">
                        {schedule.map((day, idx) => (
                            <button
                                key={idx}
                                onClick={() => {
                                    setActiveMapDay(idx);
                                    document.getElementById(`timeline-day-${idx}`)?.scrollIntoView({ behavior: 'smooth' });
                                }}
                                className={`px-5 py-2 rounded-full text-sm font-black whitespace-nowrap transition-all ${
                                    activeMapDay === idx 
                                    ? 'bg-gray-900 text-white shadow-md' 
                                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                                }`}
                            >
                                Day {day.day_index + 1}
                            </button>
                        ))}
                    </div>

                    <div className="flex-grow w-full h-full">
                        {schedule[activeMapDay] && (
                            <ItineraryMap 
                                key={`map-day-${activeMapDay}`} 
                                schedule={[schedule[activeMapDay]]} 
                            />
                        )}
                    </div>

                </div>

            </div>
        </PageTransition>
    );
}
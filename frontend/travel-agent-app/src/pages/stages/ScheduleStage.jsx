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
    RefreshCw,
    PlaneLanding, 
    BedDouble,
    GripVertical,
    Edit3,
    Undo2,
    Settings,
    ChevronDown,
    Activity
} from 'lucide-react';
import { 
    DndContext, 
    closestCorners, 
    KeyboardSensor, 
    PointerSensor, 
    useSensor, 
    useSensors,
    DragOverlay,
    defaultDropAnimationSideEffects,
    MeasuringStrategy,
    useDroppable 
} from '@dnd-kit/core';
import { 
    SortableContext, 
    verticalListSortingStrategy, 
    useSortable,
    arrayMove 
} from '@dnd-kit/sortable';
import { restrictToFirstScrollableAncestor } from '@dnd-kit/modifiers'; 
import { CSS } from '@dnd-kit/utilities';

import PageTransition from '../../components/PageTransition';
import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';
import ItineraryMap from '../../components/ItineraryMap';

// --- HELPER COMPONENTS ---

function EventCard({ event, isManualMode, dragListeners, dragAttributes, isDraggable, isOverlay, hideBucketTag }) {
    const isMeal = event.type === 'meal';
    const isFreeTime = event.type === 'free_time';
    const isLogistics = event.bucket === 'logistics';
    const isAttraction = event.type === 'attraction' && !isLogistics;

    if (isLogistics) {
        const isAirport = event.name.toLowerCase().includes('airport');
        return (
            <div className="flex items-center gap-4 py-1 ml-1 opacity-70">
                <div className="w-8 h-8 rounded-full border-2 border-dashed border-gray-300 bg-gray-50 flex items-center justify-center text-gray-400 z-10">
                    {isAirport ? <PlaneLanding size={14} /> : <BedDouble size={14} />}
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs font-black text-gray-400 tracking-wider">{event.start_time}</span>
                    <span className="text-xs font-bold text-gray-500">{event.name}</span>
                </div>
            </div>
        );
    }

    let bgClass = "bg-white border-gray-200";
    let iconBg = "bg-gray-100 text-gray-500";
    let Icon = MapPin;

    if (isMeal) {
        bgClass = "bg-orange-50/50 border-orange-100";
        iconBg = "bg-orange-100 text-orange-600";
        Icon = Utensils;
    } else if (isFreeTime) {
        bgClass = "bg-blue-50/50 border-blue-100";
        iconBg = "bg-blue-100 text-blue-600";
        Icon = Coffee;
    } else if (isAttraction) {
        Icon = MapPin;
        if (event.bucket === 'must-see' || event.bucket === 'must') {
            iconBg = "bg-purple-100 text-purple-600";
            bgClass = "bg-white border-purple-200 shadow-sm";
        } else {
            iconBg = "bg-blue-100 text-blue-600";
        }
    }

    const overlayStyles = isOverlay ? "shadow-2xl scale-105 rotate-2 cursor-grabbing ring-2 ring-blue-500" : "";

    return (
        <div className="relative flex flex-col gap-1.5 group ml-2">
            {!isOverlay && event.transit_mins > 0 && (
                <div className="flex items-center gap-2 ml-3 text-[10px] font-bold text-gray-400 uppercase tracking-widest my-0.5">
                    <TrainFront size={12} />
                    <span>~{event.transit_mins} min</span>
                </div>
            )}

            <div className={`p-3.5 rounded-xl border flex items-start gap-3 transition-all ${isDraggable && !isOverlay ? 'hover:shadow-md cursor-grab active:cursor-grabbing' : ''} ${bgClass} ${overlayStyles}`}>
                
                {isDraggable && (
                    <div 
                        {...(dragListeners || {})} 
                        {...(dragAttributes || {})}
                        className="flex items-center justify-center pt-2 -ml-1 text-gray-300 hover:text-gray-500 touch-none"
                    >
                        <GripVertical size={16} />
                    </div>
                )}

                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${iconBg}`}>
                    <Icon size={18} />
                </div>
                
                <div className="flex-grow pt-0.5 min-w-0">
                    <div className="flex justify-between items-start gap-2">
                        <div className="min-w-0">
                            {event.start_time && !isOverlay && (
                                <p className="text-[10px] font-black uppercase tracking-wider text-gray-400 mb-0.5">
                                    {event.start_time} - {event.end_time}
                                </p>
                            )}
                            <h4 className={`text-base font-black leading-tight break-words ${isMeal || isFreeTime ? 'text-gray-700' : 'text-gray-900'}`}>
                                {event.name}
                            </h4>
                        </div>
                        
                        {!hideBucketTag && isAttraction && event.bucket && (
                            <span className={`shrink-0 text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-md ${
                                event.bucket.includes('must') ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
                            }`}>
                                {event.bucket.replace('-', ' ')}
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function SortableEventCard({ event, isManualMode, hideBucketTag }) {
    const isDraggable = isManualMode && event?.type === 'attraction' && event?.bucket !== 'logistics';
    const eventName = event?.name || 'Unknown';
    const safeId = event?.id?.toString() || `fallback-${eventName.replace(/\s+/g, '-')}`;

    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
        id: safeId,
        disabled: !isDraggable,
        data: { event } 
    });

    const style = {
        transform: CSS.Translate.toString(transform),
        transition,
        opacity: isDragging ? 0.3 : 1, 
        zIndex: isDragging ? 50 : 'auto',
        position: 'relative'
    };

    return (
        <div ref={setNodeRef} style={style}>
            <EventCard 
                event={event} 
                isManualMode={isManualMode} 
                dragListeners={listeners} 
                dragAttributes={attributes} 
                isDraggable={isDraggable}
                hideBucketTag={hideBucketTag}
            />
        </div>
    );
}

function DroppableParkingLot({ excluded, isManualMode }) {
    const { setNodeRef, isOver } = useDroppable({ id: 'parking-lot' });

    const allItems = [];
    ['must', 'must-see', 'want', 'want-to-see', 'optional'].forEach(b => {
         if (excluded?.[b]) allItems.push(...excluded[b]);
    });

    const dropTargetStyle = isOver ? "ring-2 ring-blue-500 bg-blue-50/50" : "";

    if (allItems.length === 0) {
        return (
            <div 
                ref={setNodeRef} 
                className={`border-2 border-dashed border-gray-300 rounded-xl flex items-center justify-center min-h-[120px] bg-gray-50 transition-all ${dropTargetStyle}`}
            >
                <span className="text-sm font-bold text-gray-400">Drop attractions here to remove them</span>
            </div>
        );
    }

    return (
        <div ref={setNodeRef} className={`flex flex-col gap-4 min-h-[120px] rounded-xl transition-all p-2 -mx-2 ${dropTargetStyle}`}>
            {['must', 'want', 'optional'].map(bucketKey => {
                const items = excluded?.[bucketKey] || excluded?.[`${bucketKey}-see`] || [];
                if (items.length === 0) return null;

                return (
                    <div key={bucketKey} className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">{bucketKey}</h4>
                        <ul className="space-y-2">
                            {items.map((rawItem, i) => {
                                const safeItem = typeof rawItem === 'string'
                                    ? { id: `legacy-${bucketKey}-${i}`, name: rawItem, type: 'attraction', bucket: bucketKey }
                                    : rawItem;
                                return <SortableEventCard key={safeItem.id || i} event={safeItem} isManualMode={isManualMode} hideBucketTag={true} />;
                            })}
                        </ul>
                    </div>
                );
            })}
        </div>
    );
}

// ----------------------------------------------------------------------
// MAIN STAGE COMPONENT
// ----------------------------------------------------------------------

export default function ScheduleStage({ gameState, session, refresh, onBack, onNext }) {
    const [isGenerating, setIsGenerating] = useState(false);
    const [isSimulating, setIsSimulating] = useState(false);
    const [activeDragEvent, setActiveDragEvent] = useState(null);
    const [localSchedule, setLocalSchedule] = useState(null);
    const [localExcluded, setLocalExcluded] = useState(null);
    const [activeMapDay, setActiveMapDay] = useState(0); 
    const [isManualMode, setIsManualMode] = useState(false);
    
    // NEW: Controls the overlay advanced parameters dropdown visibility
    const [showAdvanced, setShowAdvanced] = useState(false);
    const advancedRef = useRef(null);
    
    const baseTripDetails = gameState?.trip_details || {};
    const [wakeupTime, setWakeupTime] = useState(baseTripDetails.wakeup_time || "08:00");
    const [lunchDuration, setLunchDuration] = useState(baseTripDetails.lunch_duration_mins || 90);

    const hasTriggered = useRef(false);
    const schedule = localSchedule || gameState?.schedule;
    const excluded = localExcluded || gameState?.excluded_pois;

    const scrollContainerRef = useRef(null);
    const scrollIntervalRef = useRef(null);

    useEffect(() => {
        return () => {
            if (scrollIntervalRef.current) clearInterval(scrollIntervalRef.current);
        };
    }, []);

    // Close advanced dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (advancedRef.current && !advancedRef.current.contains(event.target)) {
                setShowAdvanced(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor)
    );

    useEffect(() => {
        const isScheduleEmpty = !schedule || schedule.length === 0;

        if (isScheduleEmpty && !hasTriggered.current) {
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
            console.error("Failed to generate", e);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleRecalculate = async () => {
        setIsGenerating(true);
        setIsManualMode(false); 
        setShowAdvanced(false);
        try {
            const updatedDetails = {
                ...baseTripDetails,
                wakeup_time: wakeupTime,
                lunch_duration_mins: parseInt(lunchDuration, 10)
            };

            await fetchWithAuth(`${API_BASE_URL}/itinerary/schedule/details`, {
                session_id: session.id,
                trip_details: updatedDetails
            }, "POST");

            await generateSchedule();
        } catch (e) {
            console.error("Recalculation failed", e);
            setIsGenerating(false);
        }
    };

    // Placeholder routing function for Directions API stage
    const handleSyncRealTimeTransit = async () => {
        // Future endpoint trigger location
        console.log("Triggering Real-Time Distance Matrix sync...");
    };

    const stopAutoScroll = () => {
        if (scrollIntervalRef.current) {
            clearInterval(scrollIntervalRef.current);
            scrollIntervalRef.current = null;
        }
    };

    const startAutoScroll = (direction) => {
        if (scrollIntervalRef.current) return; 
        
        scrollIntervalRef.current = setInterval(() => {
            if (scrollContainerRef.current) {
                const scrollSpeed = 15; 
                scrollContainerRef.current.scrollTop += (direction === 'down' ? scrollSpeed : -scrollSpeed);
            }
        }, 16); 
    };

    const handleDragMove = (event) => {
        if (!scrollContainerRef.current || !event.active.rect.current?.translated) {
            stopAutoScroll();
            return;
        }

        const containerRect = scrollContainerRef.current.getBoundingClientRect();
        const activeRect = event.active.rect.current.translated;

        const SCROLL_ZONE_PERCENTAGE = 0.15;
        const scrollZoneHeight = containerRect.height * SCROLL_ZONE_PERCENTAGE;

        const isNearBottom = activeRect.bottom > (containerRect.bottom - scrollZoneHeight);
        const isNearTop = activeRect.top < (containerRect.top + scrollZoneHeight);

        if (isNearBottom) {
            startAutoScroll('down');
        } else if (isNearTop) {
            startAutoScroll('up');
        } else {
            stopAutoScroll();
        }
    };

    const handleDragStart = (event) => {
        const { active } = event;
        setActiveDragEvent(active.data.current?.event || null);
    };

    const handleDragCancel = () => {
        stopAutoScroll();
        setActiveDragEvent(null);
    };

    const handleDragEnd = async (event) => {
        stopAutoScroll();
        setActiveDragEvent(null); 
        
        const { active, over } = event;
        if (!over) return;

        setIsSimulating(true);

        try {
            const activeId = parseInt(active.id, 10) || active.id.toString();
            const overId = over.id.toString();
            
            const overContainerId = over.data.current?.sortable?.containerId || overId;
            const isDroppingToExcluded = overContainerId === 'parking-lot' || overId === 'parking-lot';

            const currentSchedule = localSchedule || schedule;
            let destinationDayIndex = null;

            if (!isDroppingToExcluded) {
                if (overId.startsWith('day-')) {
                    destinationDayIndex = parseInt(overId.replace('day-', ''), 10);
                } else {
                    destinationDayIndex = currentSchedule.findIndex(day => 
                        day.events.some(e => e.id?.toString() === overId)
                    );
                }

                if (destinationDayIndex === -1 || destinationDayIndex === null) {
                    setIsSimulating(false);
                    return;
                }
            }

            const userTimeline = currentSchedule.map((day, dIdx) => {
                let dayIds = day.events
                    .filter(e => e.type === 'attraction' && e.bucket !== 'logistics' && e.id?.toString() !== activeId.toString())
                    .map(e => e.id);
                
                if (!isDroppingToExcluded && dIdx === destinationDayIndex) {
                    dayIds.push(activeId); 
                }
                return dayIds;
            });

            const res = await fetchWithAuth(`${API_BASE_URL}/itinerary/schedule/custom`, {
                session_id: session.id,
                user_timeline: userTimeline
            }, "POST");

            if (res.ok) {
                const data = await res.json();
                if (data.schedule) setLocalSchedule(data.schedule);
                if (data.excluded_pois) setLocalExcluded(data.excluded_pois);
            }

        } catch (error) {
            console.error("Simulation failed", error);
        } finally {
            setIsSimulating(false);
        }
    };

    if (isGenerating || !schedule || schedule.length === 0) {
        return (
            <PageTransition className="flex flex-col items-center justify-center w-full h-full bg-gray-50">
                <div className="bg-white p-10 rounded-3xl shadow-lg border border-gray-100 flex flex-col items-center max-w-md text-center">
                    <Loader2 className="animate-spin text-blue-600 mb-6" size={32} />
                    <h2 className="text-2xl font-black text-gray-900 mb-2">Building Your Timeline</h2>
                    <p className="text-sm text-gray-500">Calculating optimal routes and opening hours...</p>
                </div>
            </PageTransition>
        );
    }

    const dropAnimation = {
        sideEffects: defaultDropAnimationSideEffects({ styles: { active: { opacity: '0.4' } } }),
    };

    const allExcludedItems = [];
    if (excluded) {
        ['must', 'want', 'optional', 'must-see', 'want-to-see'].forEach(b => {
             if(excluded[b]) {
                 excluded[b].forEach((item, i) => {
                     const safeItem = typeof item === 'string'
                        ? { id: `legacy-${b}-${i}`, name: item, type: 'attraction', bucket: b }
                        : item;
                     allExcludedItems.push(safeItem);
                 });
             }
        });
    }
    const allExcludedIds = allExcludedItems.map(item => item.id?.toString() || `fallback-${item.name}`);

    return (
        <DndContext 
            sensors={sensors} 
            modifiers={[restrictToFirstScrollableAncestor]} 
            collisionDetection={closestCorners} 
            onDragStart={handleDragStart} 
            onDragMove={handleDragMove}         
            onDragEnd={handleDragEnd}
            onDragCancel={handleDragCancel}
            measuring={{
                droppable: {
                    strategy: MeasuringStrategy.Always,
                },
            }}
        >
            <PageTransition className="flex flex-col w-full h-screen bg-gray-50 overflow-hidden relative">
                
                {/* 1. FLOATING CONTROL OVERLAY LAYER */}
                {/* Minimalist Floating Back Button */}
                <div className="absolute top-8 left-8 z-[100] pointer-events-auto">
                    <button 
                        type="button"
                        onClick={onBack} 
                        className="px-4 py-3 bg-transparent text-gray-400 hover:text-red-500 rounded-2xl font-black text-xs uppercase tracking-wider flex items-center gap-2 transition-all duration-300 group"
                    >
                        <ArrowLeft size={14} className="transform transition-transform group-hover:-translate-x-1" />
                        <span>Back</span>
                    </button>
                </div>

                {/* ADVANCED PARAMETERS DROP-DOWN CONFIGURATION */}
                <div ref={advancedRef} className="absolute top-8 left-1/2 -translate-x-1/2 z-[100] pointer-events-auto flex flex-col items-center">
                    <button
                        type="button"
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className={`px-5 py-3 rounded-2xl font-black text-xs uppercase tracking-wider flex items-center gap-2 transition-all duration-300 border ${
                            showAdvanced 
                                ? 'bg-gray-900 text-white border-transparent shadow-lg' 
                                : 'bg-white/80 backdrop-blur-md text-gray-500 hover:text-gray-900 border-gray-200 shadow-sm'
                        }`}
                    >
                        <Settings size={14} className={showAdvanced ? 'animate-spin' : ''} />
                        <span>Advanced Options</span>
                        <ChevronDown size={14} className={`transform transition-transform duration-300 ${showAdvanced ? 'rotate-180' : ''}`} />
                    </button>

                    {/* Dropdown Menu Panel Card */}
                    {showAdvanced && (
                        <div className="mt-2 bg-white border border-gray-100 rounded-3xl shadow-2xl p-6 w-80 sm:w-96 flex flex-col gap-5 animate-fadeIn">
                            <div className="flex items-center justify-between gap-4 border-b border-gray-100 pb-3">
                                <h4 className="text-xs font-black uppercase tracking-wider text-gray-400">Timeline Engine Parameters</h4>
                            </div>

                            {/* Inputs Block */}
                            <div className="flex gap-4 items-center justify-between">
                                <div className="flex flex-col gap-1.5 flex-1">
                                    <label className="text-[10px] font-black uppercase tracking-wider text-gray-400 flex items-center gap-1">
                                        <Sun size={12} /> Start Time
                                    </label>
                                    <input 
                                        type="time" 
                                        value={wakeupTime} 
                                        onChange={(e) => setWakeupTime(e.target.value)} 
                                        className="bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs font-bold text-gray-800 outline-none focus:ring-2 focus:ring-blue-500 w-full" 
                                    />
                                </div>
                                <div className="flex flex-col gap-1.5 flex-1">
                                    <label className="text-[10px] font-black uppercase tracking-wider text-gray-400 flex items-center gap-1">
                                        <Utensils size={12} /> Lunch Break
                                    </label>
                                    <select 
                                        value={lunchDuration} 
                                        onChange={(e) => setLunchDuration(e.target.value)} 
                                        className="bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs font-bold text-gray-800 outline-none focus:ring-2 focus:ring-blue-500 w-full cursor-pointer"
                                    >
                                        <option value="45">45 Mins</option>
                                        <option value="60">1 Hour</option>
                                        <option value="90">1.5 Hours</option>
                                        <option value="120">2 Hours</option>
                                    </select>
                                </div>
                            </div>

                            {/* Action Operations Stack */}
                            <div className="flex flex-col gap-2 mt-2">
                                <button 
                                    type="button"
                                    onClick={handleRecalculate} 
                                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-black text-xs uppercase tracking-wider py-3 rounded-xl flex items-center justify-center gap-2 shadow-sm transition-all"
                                >
                                    <RefreshCw size={14} />
                                    Recalculate Configuration
                                </button>

                                <div className="h-px bg-gray-100 my-1" />

                                {isManualMode ? (
                                    <button 
                                        type="button"
                                        onClick={() => { setIsManualMode(false); setShowAdvanced(false); generateSchedule(); }}
                                        className="w-full bg-red-50 text-red-600 hover:bg-red-100 font-black text-xs uppercase tracking-wider py-3 rounded-xl flex items-center justify-center gap-2 transition"
                                    >
                                        <Undo2 size={14} /> Revert to AI Draft
                                    </button>
                                ) : (
                                    <button 
                                        type="button"
                                        onClick={() => { setIsManualMode(true); setShowAdvanced(false); }}
                                        className="w-full bg-blue-50 text-blue-600 hover:bg-blue-100 font-black text-xs uppercase tracking-wider py-3 rounded-xl flex items-center justify-center gap-2 transition"
                                    >
                                        <Edit3 size={14} /> Customize Manually
                                    </button>
                                )}

                                <button 
                                    type="button"
                                    onClick={handleSyncRealTimeTransit} 
                                    className="w-full bg-emerald-50 text-emerald-600 hover:bg-emerald-100 font-black text-xs uppercase tracking-wider py-3 rounded-xl flex items-center justify-center gap-2 transition"
                                >
                                    <Activity size={14} />
                                    ⚡ Sync Real-Time Routing
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Minimalist Floating Forward/Overview Button */}
                <div className="absolute top-8 right-8 z-[100] pointer-events-auto">
                    <button 
                        type="button"
                        onClick={onNext} 
                        className="px-4 py-3 bg-transparent text-gray-400 hover:text-blue-500 rounded-2xl font-black text-xs uppercase tracking-wider flex items-center gap-2 transition-all duration-300 group"
                    >
                        <span>Overview</span>
                        <ArrowRight size={14} className="transform transition-transform group-hover:translate-x-1" />
                    </button>
                </div>

                {/* 2. DUAL COLUMNS WORKSPACE CONTAINER */}
                <div className="flex flex-row flex-1 overflow-hidden relative min-h-0 pt-24">
                    
                    {isSimulating && (
                        <div className="absolute inset-0 bg-white/60 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                            <Loader2 className="animate-spin text-blue-600 mb-4" size={40} />
                            <h3 className="font-black text-lg text-gray-900">Simulating Routes...</h3>
                        </div>
                    )}

                    {/* LEFT SIDEBAR: TIMELINE LIST */}
                    <div ref={scrollContainerRef} id="scrollable-timeline" className="w-full lg:w-[45%] flex-1 h-full overflow-y-auto z-10 bg-gray-50 relative">
                        <div className="p-8 max-w-xl mx-auto">
                            
                            <div className="mb-8">
                                <h1 className="text-4xl font-black text-gray-900 tracking-tight">Your Itinerary Draft</h1>
                                <p className="text-gray-400 mt-2 font-medium text-xs">
                                    {isManualMode 
                                        ? "DND Canvas Active: Rearrange attractions freely. Transit windows self-correct dynamically." 
                                        : "Review calculated schedule constraints. Adjust engine dropdown variables to regenerate parameters."}
                                </p>
                            </div>

                            {/* Timeline Stack */}
                            <div className="space-y-12">
                                {schedule.map((day, idx) => {
                                    const dateObj = new Date(day.date);
                                    const safeDayId = `day-${idx}`;
                                    
                                    const draggableIds = day.events
                                        .filter(e => e.type === 'attraction' && e.bucket !== 'logistics')
                                        .map(e => e.id?.toString() || `fallback-${e.name?.replace(/\s+/g, '-') || Math.random()}`);

                                    return (
                                        <div key={idx} id={safeDayId} className="relative border-2 border-transparent hover:border-blue-100 rounded-2xl transition p-2 -mx-2">
                                            <div className="sticky top-0 z-10 bg-gray-50/90 backdrop-blur-md py-4 mb-2 border-b border-gray-200 flex items-center gap-3">
                                                <div className="bg-gray-900 text-white w-10 h-10 rounded-xl flex items-center justify-center font-black shadow-sm">{day.day_index + 1}</div>
                                                <div>
                                                    <h3 className="text-xl font-black text-gray-900">{dateObj.toLocaleDateString('en-US', { weekday: 'long' })}</h3>
                                                </div>
                                            </div>

                                            <SortableContext id={safeDayId} items={draggableIds} strategy={verticalListSortingStrategy}>
                                                <div className="pl-4 border-l-2 border-gray-200 ml-4 space-y-4 py-2 min-h-[50px]">
                                                    {day.events.map((evt, eIdx) => (
                                                        <SortableEventCard key={`${evt.id || eIdx}-${eIdx}`} event={evt} isManualMode={isManualMode} />
                                                    ))}
                                                </div>
                                            </SortableContext>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* PARKING LOT */}
                            {(allExcludedItems.length > 0 || isManualMode) && (
                                <div className="mt-16 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                                    <h3 className="text-lg font-black text-gray-900 flex items-center gap-2"><CalendarDays size={20}/> Dropped Attractions</h3>
                                    <p className="text-xs text-gray-500 mb-4">
                                        {isManualMode ? "Drop attractions here to remove them from your timeline." : "These didn't fit in your timeline."}
                                    </p>

                                    <SortableContext id="parking-lot" items={allExcludedIds} strategy={verticalListSortingStrategy}>
                                        <DroppableParkingLot excluded={excluded} isManualMode={isManualMode} />
                                    </SortableContext>
                                </div>
                            )}

                        </div>
                    </div>

                    {/* RIGHT SIDEBAR: FULL LAYER MAP CANVAS */}
                    <div className="hidden lg:flex flex-col lg:w-[55%] relative bg-gray-200 border-l border-gray-200 shadow-inner z-0">
                        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/90 backdrop-blur-md p-1.5 rounded-full shadow-lg border border-gray-200 flex gap-1 overflow-x-auto max-w-[90%]">
                            {schedule.map((day, idx) => (
                                <button
                                    type="button"
                                    key={idx}
                                    onClick={() => {
                                        setActiveMapDay(idx);
                                        document.getElementById(`timeline-day-${idx}`)?.scrollIntoView({ behavior: 'smooth' });
                                    }}
                                    className={`px-5 py-2 rounded-full text-sm font-black whitespace-nowrap transition-all ${
                                        activeMapDay === idx ? 'bg-gray-900 text-white shadow-md' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                                    }`}
                                >
                                    Day {day.day_index + 1}
                                </button>
                            ))}
                        </div>

                        <div className="flex-grow w-full h-full">
                            {schedule[activeMapDay] && (
                                <ItineraryMap key={`map-day-${activeMapDay}`} schedule={[schedule[activeMapDay]]} />
                            )}
                        </div>
                    </div>

                </div>

            </PageTransition>

            {/* FLOATING ACTIVE DND ENGINE OVERLAY GLUE LAYER */}
            <DragOverlay dropAnimation={dropAnimation}>
                {activeDragEvent ? (
                    <div className="w-[350px]"> 
                        <EventCard 
                            event={activeDragEvent} 
                            isManualMode={true} 
                            isDraggable={true} 
                            isOverlay={true} 
                        />
                    </div>
                ) : null}
            </DragOverlay>

        </DndContext>
    );
}
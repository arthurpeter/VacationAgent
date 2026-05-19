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
    Undo2
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
    useDroppable // <-- NEW: Imported useDroppable
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

// --- NEW: THE UNIFIED PARKING LOT COMPONENT ---
function DroppableParkingLot({ excluded, isManualMode }) {
    // This tells dnd-kit that this entire visual box is a single drop target
    const { setNodeRef, isOver } = useDroppable({ id: 'parking-lot' });

    const allItems = [];
    ['must', 'must-see', 'want', 'want-to-see', 'optional'].forEach(b => {
         if (excluded?.[b]) allItems.push(...excluded[b]);
    });

    // Visually highlight the box when dragging over it
    const dropTargetStyle = isOver ? "ring-2 ring-blue-500 bg-blue-50/50" : "";

    // 1. The Empty State
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

    // 2. The Populated State (Visually sorted, but physically one target)
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

// --- MAIN COMPONENT ---

export default function ScheduleStage({ gameState, session, refresh, onBack, onNext }) {
    const [isGenerating, setIsGenerating] = useState(false);
    const [isSimulating, setIsSimulating] = useState(false);
    const [activeDragEvent, setActiveDragEvent] = useState(null);
    const [localSchedule, setLocalSchedule] = useState(null);
    const [localExcluded, setLocalExcluded] = useState(null);
    const [activeMapDay, setActiveMapDay] = useState(0); 
    const [isManualMode, setIsManualMode] = useState(false);
    
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
            
            // FIX: Check if we dropped over our new unified parking lot
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
                // Filter out the active item regardless of where it came from
                let dayIds = day.events
                    .filter(e => e.type === 'attraction' && e.bucket !== 'logistics' && e.id?.toString() !== activeId.toString())
                    .map(e => e.id);
                
                // Only push it to a day if we didn't drop it in the trash/parking lot
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

    // Flatten all excluded IDs so the SortableContext knows what items exist in the parking lot
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
            <PageTransition className="flex flex-col w-full h-screen bg-gray-50 overflow-hidden">
                
                <div className="bg-white border-b border-gray-200 p-4 shadow-sm shrink-0 flex items-center justify-between z-20">
                    <button onClick={onBack} className="flex items-center gap-2 text-gray-500 hover:text-blue-600 font-bold px-4 py-2">
                        <ArrowLeft size={18} /> Back
                    </button>
                    
                    <div className="flex gap-4">
                        {isManualMode ? (
                            <button 
                                onClick={() => { setIsManualMode(false); generateSchedule(); }}
                                className="px-4 py-2 bg-red-50 text-red-600 rounded-lg font-bold flex items-center gap-2 transition hover:bg-red-100"
                            >
                                <Undo2 size={16} /> Revert to AI Draft
                            </button>
                        ) : (
                            <button 
                                onClick={() => setIsManualMode(true)}
                                className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg font-bold flex items-center gap-2 transition hover:bg-blue-100"
                            >
                                <Edit3 size={16} /> Customize Manually
                            </button>
                        )}

                        <button onClick={onNext} className="px-6 py-2 bg-gray-900 hover:bg-black text-white rounded-lg font-bold shadow-md flex items-center gap-2">
                            Finalize Trip <ArrowRight size={18} />
                        </button>
                    </div>
                </div>

                <div className="flex flex-row flex-1 overflow-hidden relative min-h-0">
                    
                    {isSimulating && (
                        <div className="absolute inset-0 bg-white/60 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                            <Loader2 className="animate-spin text-blue-600 mb-4" size={40} />
                            <h3 className="font-black text-lg text-gray-900">Simulating Routes...</h3>
                        </div>
                    )}

                    <div ref={scrollContainerRef} id="scrollable-timeline" className="w-full lg:w-[45%] flex-1 h-full overflow-y-auto z-10 bg-gray-50 relative">
                        <div className="p-8 max-w-xl mx-auto">
                            
                            <div className="mb-6">
                                <h1 className="text-4xl font-black text-gray-900 tracking-tight">Your Itinerary Draft</h1>
                                <p className="text-gray-500 mt-2 font-medium">
                                    {isManualMode 
                                        ? "Drag attractions to rearrange them. Transit times will auto-adjust." 
                                        : "Review your daily timeline. Adjust parameters to regenerate."}
                                </p>
                            </div>

                            {!isManualMode && (
                                <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm mb-10 flex flex-col sm:flex-row items-center justify-between gap-4 sticky top-0 z-40">
                                    <div className="flex items-center gap-6">
                                        <div className="flex flex-col gap-1">
                                            <label className="text-[10px] font-black uppercase text-gray-400 flex items-center gap-1"><Sun size={12} /> Start Time</label>
                                            <input type="time" value={wakeupTime} onChange={(e) => setWakeupTime(e.target.value)} className="bg-gray-50 border rounded-lg px-3 py-1.5 text-sm font-bold" />
                                        </div>
                                        <div className="flex flex-col gap-1">
                                            <label className="text-[10px] font-black uppercase text-gray-400 flex items-center gap-1"><Utensils size={12} /> Lunch</label>
                                            <select value={lunchDuration} onChange={(e) => setLunchDuration(e.target.value)} className="bg-gray-50 border rounded-lg px-3 py-1.5 text-sm font-bold cursor-pointer">
                                                <option value="45">45 Mins</option><option value="60">1 Hour</option><option value="90">1.5 Hours</option><option value="120">2 Hours</option>
                                            </select>
                                        </div>
                                    </div>
                                    <button onClick={handleRecalculate} className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-2 rounded-xl flex items-center gap-2"><RefreshCw size={16} /> Recalculate</button>
                                </div>
                            )}

                            {/* The Timeline */}
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

                            {/* NEW: THE UNIFIED PARKING LOT */}
                            {(allExcludedItems.length > 0 || isManualMode) && (
                                <div className="mt-16 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                                    <h3 className="text-lg font-black text-gray-900 flex items-center gap-2"><CalendarDays size={20}/> Dropped Attractions</h3>
                                    <p className="text-xs text-gray-500 mb-4">
                                        {isManualMode ? "Drop attractions here to remove them from your timeline." : "These didn't fit in your timeline."}
                                    </p>

                                    {/* The single wrapper Context for the whole parking lot */}
                                    <SortableContext id="parking-lot" items={allExcludedIds} strategy={verticalListSortingStrategy}>
                                        <DroppableParkingLot excluded={excluded} isManualMode={isManualMode} />
                                    </SortableContext>
                                </div>
                            )}

                        </div>
                    </div>

                    {/* RIGHT PANEL: MAP */}
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

            {/* THE DRAG OVERLAY */}
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
import React, { useEffect, useMemo, useState } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft, ArrowRight, ClipboardList, MapPin, Route, Sparkles } from 'lucide-react';

import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';
import PageTransition from '../../components/PageTransition';

const STAGES = [
  { id: 1, label: 'Prioritize', description: 'Bucket your must-dos' },
  { id: 2, label: 'Logistics', description: 'Transit & pace' },
  { id: 3, label: 'Allocate', description: 'Cluster into days' },
  { id: 4, label: 'Edit', description: 'Adjust the timeline' },
  { id: 5, label: 'Optimize', description: 'Route each day' }
];

const POI_SUGGESTIONS = [
  {
    id: 'poi-louvre',
    name: 'Louvre Museum',
    summary: 'Masterpieces, iconic art, and the Mona Lisa.',
    durationMins: 180,
    todPreference: 'morning',
    coordinates: { lat: 48.8606, lng: 2.3376 }
  },
  {
    id: 'poi-seine',
    name: 'Seine River Cruise',
    summary: 'A relaxed cruise with landmark views.',
    durationMins: 90,
    todPreference: 'afternoon',
    coordinates: { lat: 48.8575, lng: 2.3050 }
  },
  {
    id: 'poi-montmartre',
    name: 'Montmartre Walk',
    summary: 'Hillside cafes, art studios, and basilica views.',
    durationMins: 120,
    todPreference: 'morning',
    coordinates: { lat: 48.8867, lng: 2.3431 }
  },
  {
    id: 'poi-latin-quarter',
    name: 'Latin Quarter Food Crawl',
    summary: 'Local bakeries, markets, and bistros.',
    durationMins: 150,
    todPreference: 'evening',
    coordinates: { lat: 48.8493, lng: 2.3470 }
  },
  {
    id: 'poi-orsay',
    name: 'Musée d’Orsay',
    summary: 'Impressionist art in a historic rail station.',
    durationMins: 150,
    todPreference: 'morning',
    coordinates: { lat: 48.8600, lng: 2.3266 }
  },
  {
    id: 'poi-marais',
    name: 'Le Marais Shopping',
    summary: 'Boutiques, galleries, and hidden courtyards.',
    durationMins: 120,
    todPreference: 'afternoon',
    coordinates: { lat: 48.8579, lng: 2.3626 }
  },
  {
    id: 'poi-versailles',
    name: 'Versailles Day Trip',
    summary: 'Palace tour and garden stroll.',
    durationMins: 360,
    todPreference: 'morning',
    coordinates: { lat: 48.8049, lng: 2.1204 }
  },
  {
    id: 'poi-eiffel',
    name: 'Eiffel Tower Visit',
    summary: 'Sunset views and photo ops.',
    durationMins: 120,
    todPreference: 'evening',
    coordinates: { lat: 48.8584, lng: 2.2945 }
  }
];

const PACE_OPTIONS = [
  { value: 'relaxed', label: 'Relaxed', description: 'Max ~6 hours/day' },
  { value: 'balanced', label: 'Balanced', description: 'Max ~8 hours/day' },
  { value: 'packed', label: 'Packed', description: 'Max ~10 hours/day' }
];

const TRANSIT_OPTIONS = [
  { value: 'walk', label: 'Walk' },
  { value: 'drive', label: 'Rent Car' },
  { value: 'transit', label: 'Public Transit' }
];

const getPriorityLabel = (priority) => {
  if (priority === 1) return 'Must Do';
  if (priority === 2) return 'Want to Do';
  return 'If Time Permits';
};

const formatDuration = (mins) => {
  const hours = Math.floor(mins / 60);
  const minutes = mins % 60;
  if (hours === 0) return `${minutes}m`;
  if (minutes === 0) return `${hours}h`;
  return `${hours}h ${minutes}m`;
};

const TransitStrategyCard = ({ strategy }) => {
  if (!strategy) {
    return (
      <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6 shadow-sm">
        <h4 className="text-[11px] font-black tracking-widest text-blue-600 uppercase mb-2">
          Transit Snapshot
        </h4>
        <p className="text-sm text-gray-600 leading-relaxed">
          Ask the itinerary agent for a local transit tip, or proceed with your preferred travel style.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6 transition-all hover:shadow-md">
      <div className="flex items-start gap-4">
        <div className="bg-blue-600 text-white p-3 rounded-xl shadow-md mt-1 shrink-0">
          <MapPin size={20} />
        </div>
        <div>
          <h4 className="text-[11px] font-black tracking-widest text-blue-600 uppercase mb-1.5">
            Local Transit Strategy
          </h4>
          <h3 className="text-xl font-black text-gray-900 mb-1.5">
            {strategy.pass_name || 'Transit Recommendation'}
            {strategy.price ? <span className="text-gray-500 font-medium"> — {strategy.price}</span> : null}
          </h3>
          <div className="text-gray-600 text-sm leading-relaxed max-w-xl">
            <ReactMarkdown>{strategy.description || ''}</ReactMarkdown>
          </div>
        </div>
      </div>

      {strategy.purchase_url && (
        <a
          href={strategy.purchase_url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 w-full md:w-auto text-center bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition-all shadow-sm hover:shadow hover:-translate-y-0.5"
        >
          Get Official Pass
        </a>
      )}
    </div>
  );
};

export default function ItineraryStage() {
  const { sessionData } = useOutletContext();
  const params = useParams();
  const session = sessionData?.data || sessionData;
  const sessionId = session?.id || params.sessionId || params.id;

  const [currentStage, setCurrentStage] = useState(1);
  const [tripState, setTripState] = useState({
    preferences: {
      transitMode: 'transit',
      pace: 'balanced'
    },
    unscheduled: [],
    days: []
  });
  const [transitStrategy, setTransitStrategy] = useState(null);
  const [manualDays, setManualDays] = useState(1);
  const [isAllocating, setIsAllocating] = useState(false);
  const [allocationError, setAllocationError] = useState(null);
  const [optimizingDayIndex, setOptimizingDayIndex] = useState(null);
  const [optimizationErrors, setOptimizationErrors] = useState({});

  useEffect(() => {
    const loadTransitStrategy = async () => {
      if (!sessionId) return;
      try {
        const response = await fetchWithAuth(`${API_BASE_URL}/chat/itinerary/messages/${sessionId}`, {}, 'GET');
        if (response && response.ok) {
          const data = await response.json();
          if (data.transit_strategy && Object.keys(data.transit_strategy).length > 0) {
            setTransitStrategy(data.transit_strategy);
          }
        }
      } catch (error) {
        console.error('Failed to load transit strategy:', error);
      }
    };

    loadTransitStrategy();
  }, [sessionId]);

  const computedDays = useMemo(() => {
    if (!session?.from_date || !session?.to_date) return 1;
    const start = new Date(session.from_date);
    const end = new Date(session.to_date);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 1;
    const diffMs = end.getTime() - start.getTime();
    if (diffMs < 0) return 1;
    return Math.max(1, Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1);
  }, [session?.from_date, session?.to_date]);

  useEffect(() => {
    setManualDays(computedDays);
  }, [computedDays]);

  const selectedPoiIds = useMemo(() => {
    const ids = new Set(tripState.unscheduled.map((poi) => poi.id));
    tripState.days.forEach((day) => {
      day.forEach((poi) => ids.add(poi.id));
    });
    return ids;
  }, [tripState.unscheduled, tripState.days]);

  const sortedBucket = useMemo(() => {
    return [...tripState.unscheduled].sort((a, b) => a.priority - b.priority);
  }, [tripState.unscheduled]);

  const updateTripPreferences = (updates) => {
    setTripState((prev) => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        ...updates
      }
    }));
  };

  const updatePoiPriority = (poi, priority) => {
    setTripState((prev) => {
      const existingIndex = prev.unscheduled.findIndex((item) => item.id === poi.id);
      const nextUnscheduled = [...prev.unscheduled];

      const poiPayload = {
        id: poi.id,
        name: poi.name,
        priority,
        durationMins: poi.durationMins,
        todPreference: poi.todPreference,
        coordinates: poi.coordinates
      };

      if (existingIndex >= 0) {
        nextUnscheduled[existingIndex] = { ...nextUnscheduled[existingIndex], priority };
      } else {
        nextUnscheduled.push(poiPayload);
      }

      return {
        ...prev,
        unscheduled: nextUnscheduled
      };
    });
  };

  const removeFromBucket = (poiId) => {
    setTripState((prev) => ({
      ...prev,
      unscheduled: prev.unscheduled.filter((poi) => poi.id !== poiId)
    }));
  };

  const ensureDayCount = (days, count) => {
    const nextDays = days.map((day) => [...day]);
    while (nextDays.length < count) {
      nextDays.push([]);
    }
    return nextDays;
  };

  const handleAllocateItinerary = async () => {
    if (tripState.unscheduled.length === 0) {
      setAllocationError('Select at least one place before generating the itinerary.');
      return;
    }
    if (!manualDays || manualDays < 1) {
      setAllocationError('Please set a valid number of days.');
      return;
    }

    setIsAllocating(true);
    setAllocationError(null);
    const payload = {
      unscheduled: tripState.unscheduled,
      days: manualDays,
      transitMode: tripState.preferences.transitMode,
      pace: tripState.preferences.pace
    };
    console.log('Itinerary allocate payload:', payload);

    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/itinerary/allocate`, payload, 'POST');
      if (!response) {
        throw new Error('No response received for allocation.');
      }
      if (!response.ok) {
        throw new Error(`Allocation failed with status ${response.status}`);
      }
      const data = await response.json();
      console.log('Itinerary allocate response:', data);

      setTripState((prev) => ({
        ...prev,
        days: data.days || [],
        unscheduled: data.unscheduled || []
      }));
      setCurrentStage(4);
    } catch (error) {
      console.error('Failed to allocate itinerary:', error);
      setAllocationError('Unable to allocate the itinerary. Please try again.');
    } finally {
      setIsAllocating(false);
    }
  };

  const moveUnscheduledToDay = (poiId, dayIndex) => {
    setTripState((prev) => {
      const poi = prev.unscheduled.find((item) => item.id === poiId);
      if (!poi) return prev;

      const targetCount = Math.max(manualDays, prev.days.length || 0);
      const nextDays = ensureDayCount(prev.days, targetCount);
      nextDays[dayIndex] = [...nextDays[dayIndex], poi];

      return {
        ...prev,
        unscheduled: prev.unscheduled.filter((item) => item.id !== poiId),
        days: nextDays
      };
    });
  };

  const moveDayToUnscheduled = (dayIndex, poiIndex) => {
    setTripState((prev) => {
      if (!prev.days[dayIndex]) return prev;
      const targetCount = Math.max(manualDays, prev.days.length || 0);
      const nextDays = ensureDayCount(prev.days, targetCount);
      const dayItems = [...nextDays[dayIndex]];
      const [removed] = dayItems.splice(poiIndex, 1);
      if (!removed) return prev;

      nextDays[dayIndex] = dayItems;

      return {
        ...prev,
        unscheduled: [...prev.unscheduled, removed],
        days: nextDays
      };
    });
  };

  const moveDayToDay = (fromDay, toDay, poiIndex) => {
    setTripState((prev) => {
      if (!prev.days[fromDay]) return prev;
      const targetCount = Math.max(manualDays, prev.days.length || 0);
      const nextDays = ensureDayCount(prev.days, targetCount);
      const originItems = [...nextDays[fromDay]];
      const [moved] = originItems.splice(poiIndex, 1);
      if (!moved) return prev;

      nextDays[fromDay] = originItems;
      nextDays[toDay] = [...nextDays[toDay], moved];

      return {
        ...prev,
        days: nextDays
      };
    });
  };

  const movePoiWithinDay = (dayIndex, poiIndex, direction) => {
    setTripState((prev) => {
      if (!prev.days[dayIndex]) return prev;
      const targetCount = Math.max(manualDays, prev.days.length || 0);
      const nextDays = ensureDayCount(prev.days, targetCount);
      const dayItems = [...nextDays[dayIndex]];
      const nextIndex = poiIndex + direction;
      if (nextIndex < 0 || nextIndex >= dayItems.length) return prev;

      const [moved] = dayItems.splice(poiIndex, 1);
      dayItems.splice(nextIndex, 0, moved);
      nextDays[dayIndex] = dayItems;

      return {
        ...prev,
        days: nextDays
      };
    });
  };

  const handleOptimizeDay = async (dayIndex) => {
    const dayItems = tripState.days[dayIndex] || [];
    if (dayItems.length < 2) return;

    setOptimizingDayIndex(dayIndex);
    setOptimizationErrors((prev) => ({ ...prev, [dayIndex]: null }));

    const payload = {
      pois: dayItems,
      transitMode: tripState.preferences.transitMode
    };
    console.log('Route-day payload:', payload);

    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/itinerary/route-day`, payload, 'POST');
      if (!response) {
        throw new Error('No response received for route optimization.');
      }
      if (!response.ok) {
        throw new Error(`Routing failed with status ${response.status}`);
      }
      const data = await response.json();
      console.log('Route-day response:', data);

      setTripState((prev) => {
        const targetCount = Math.max(manualDays, prev.days.length || 0);
        const nextDays = ensureDayCount(prev.days, targetCount);
        nextDays[dayIndex] = data;
        return {
          ...prev,
          days: nextDays
        };
      });
    } catch (error) {
      console.error('Failed to optimize route:', error);
      setOptimizationErrors((prev) => ({
        ...prev,
        [dayIndex]: 'Unable to optimize this day. Keeping your current order.'
      }));
    } finally {
      setOptimizingDayIndex(null);
    }
  };

  const renderStageIndicator = () => (
    <div className="flex flex-wrap gap-3">
      {STAGES.map((stage) => (
        <button
          key={stage.id}
          type="button"
          onClick={() => setCurrentStage(stage.id)}
          className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-left transition ${
            currentStage === stage.id
              ? 'bg-blue-50 border-blue-200 text-blue-700 shadow-sm'
              : 'bg-white border-gray-200 text-gray-600 hover:border-blue-200 hover:text-blue-600'
          }`}
        >
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-black text-sm ${
            currentStage === stage.id ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500'
          }`}>
            {stage.id}
          </div>
          <div>
            <div className="text-sm font-bold">{stage.label}</div>
            <div className="text-[11px] text-gray-500">{stage.description}</div>
          </div>
        </button>
      ))}
    </div>
  );

  const renderStageOne = () => (
    <div className="grid grid-cols-1 lg:grid-cols-[2fr,1fr] gap-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-black text-gray-800 flex items-center gap-2">
              <ClipboardList size={20} className="text-blue-600" />
              Pick & Prioritize
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Choose what you want to do. We’ll cluster these into days later.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {POI_SUGGESTIONS.map((poi) => {
            const selectedPoi = tripState.unscheduled.find((item) => item.id === poi.id);
            const isScheduled = selectedPoiIds.has(poi.id) && !selectedPoi;
            return (
              <div key={poi.id} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition group">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-gray-800">{poi.name}</h3>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">{poi.summary}</p>
                  </div>
                  <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">
                    {formatDuration(poi.durationMins)}
                  </div>
                </div>

                {selectedPoi ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-blue-50 text-blue-700 mb-3">
                    {getPriorityLabel(selectedPoi.priority)}
                  </span>
                ) : null}

                {isScheduled && !selectedPoi ? (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-green-50 text-green-700 mb-3">
                    Scheduled
                  </span>
                ) : null}

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {[1, 2, 3].map((priority) => (
                    <button
                      key={priority}
                      type="button"
                      disabled={isScheduled}
                      onClick={() => updatePoiPriority(poi, priority)}
                      className={`py-2 rounded-lg border text-xs font-bold transition ${
                        selectedPoi?.priority === priority
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white border-gray-200 text-gray-600 hover:bg-blue-50 hover:text-blue-600'
                      } ${isScheduled ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {priority === 1 ? '🥇 Must Do' : priority === 2 ? '👍 Want To' : '🤷 If Time'}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 h-fit">
        <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest mb-4">Prioritized Bucket</h3>
        {sortedBucket.length === 0 ? (
          <p className="text-sm text-gray-500">No places added yet. Pick your must-dos to start.</p>
        ) : (
          <div className="space-y-3">
            {sortedBucket.map((poi) => (
              <div key={poi.id} className="bg-gray-50 border border-gray-100 rounded-xl p-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-bold text-gray-800">{poi.name}</div>
                    <div className="text-[10px] text-gray-400 uppercase tracking-widest">
                      {getPriorityLabel(poi.priority)} · {formatDuration(poi.durationMins)}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFromBucket(poi.id)}
                    className="text-xs font-bold text-red-500 hover:underline"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderStageTwo = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-xl font-black text-gray-800 flex items-center gap-2 mb-2">
          <Route size={20} className="text-blue-600" />
          Logistics Hub
        </h2>
        <p className="text-sm text-gray-500">Choose how you want to move each day.</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          {TRANSIT_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => updateTripPreferences({ transitMode: option.value })}
              className={`p-4 rounded-xl border-2 transition text-left ${
                tripState.preferences.transitMode === option.value
                  ? 'border-blue-500 ring-2 ring-blue-200 bg-blue-50'
                  : 'border-gray-100 hover:border-blue-200 hover:bg-blue-50'
              }`}
            >
              <div className="text-sm font-black text-gray-800">{option.label}</div>
              <div className="text-xs text-gray-500 mt-1">Primary mode</div>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          {PACE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => updateTripPreferences({ pace: option.value })}
              className={`p-4 rounded-xl border-2 transition text-left ${
                tripState.preferences.pace === option.value
                  ? 'border-blue-500 ring-2 ring-blue-200 bg-blue-50'
                  : 'border-gray-100 hover:border-blue-200 hover:bg-blue-50'
              }`}
            >
              <div className="text-sm font-black text-gray-800">{option.label}</div>
              <div className="text-xs text-gray-500 mt-1">{option.description}</div>
            </button>
          ))}
        </div>
      </div>

      <TransitStrategyCard strategy={transitStrategy} />
    </div>
  );

  const renderStageThree = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-xl font-black text-gray-800 flex items-center gap-2 mb-2">
          <Sparkles size={20} className="text-blue-600" />
          Smart Allocator
        </h2>
        <p className="text-sm text-gray-500">
          We’ll cluster your picks into day-sized groups based on location and time.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4">
            <div className="text-xs text-gray-400 uppercase tracking-widest font-bold">Stops Selected</div>
            <div className="text-2xl font-black text-gray-800 mt-2">{tripState.unscheduled.length}</div>
          </div>
          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4">
            <div className="text-xs text-gray-400 uppercase tracking-widest font-bold">Transit Mode</div>
            <div className="text-lg font-bold text-gray-800 mt-2 capitalize">{tripState.preferences.transitMode}</div>
          </div>
          <div className="bg-gray-50 border border-gray-100 rounded-xl p-4">
            <div className="text-xs text-gray-400 uppercase tracking-widest font-bold">Pace</div>
            <div className="text-lg font-bold text-gray-800 mt-2 capitalize">{tripState.preferences.pace}</div>
          </div>
        </div>

        <div className="mt-6 flex flex-col md:flex-row md:items-end gap-4">
          <div className="flex-1">
            <label className="text-xs font-bold text-gray-500 uppercase tracking-widest">Trip Days</label>
            <div className="mt-2 flex items-center gap-3">
              <input
                type="number"
                min="1"
                value={manualDays}
                onChange={(e) => setManualDays(Math.max(1, Number(e.target.value) || 1))}
                className="w-24 rounded-lg border border-gray-200 px-3 py-2 text-sm font-bold text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-500">Auto-detected: {computedDays} days</span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleAllocateItinerary}
            disabled={isAllocating}
            className="flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 text-white font-black rounded-xl hover:bg-blue-700 transition disabled:opacity-60 disabled:cursor-not-allowed shadow-sm"
          >
            {isAllocating ? 'Allocating...' : 'Generate Itinerary'}
          </button>
        </div>

        {allocationError && (
          <div className="mt-4 bg-red-50 border border-red-100 text-red-600 text-sm font-medium rounded-xl px-4 py-3">
            {allocationError}
          </div>
        )}
      </div>
    </div>
  );

  const renderTimelineBoard = (showOptimize) => {
    if (tripState.days.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <h2 className="text-xl font-black text-gray-800">Generate an Itinerary First</h2>
          <p className="text-sm mt-2">Use the Smart Allocator to create day columns.</p>
        </div>
      );
    }

    const dayCount = Math.max(tripState.days.length, manualDays);
    const dayIndices = Array.from({ length: dayCount }, (_, idx) => idx);

    return (
      <div className="space-y-4">
        <p className="text-sm text-gray-500">
          Use the controls below to move items between days. This keeps the MVP lightweight without extra drag-and-drop dependencies.
        </p>
        <div className="grid grid-cols-1 xl:grid-cols-[1fr,3fr] gap-4">
          <div className="bg-gray-50 rounded-2xl border border-gray-200 p-4 h-fit">
            <h3 className="text-sm font-black text-gray-800 uppercase tracking-widest mb-4">
              Unscheduled / Parking Lot
            </h3>
            {tripState.unscheduled.length === 0 ? (
              <p className="text-sm text-gray-500">All selected places are scheduled.</p>
            ) : (
              <div className="space-y-3">
                {tripState.unscheduled.map((poi) => (
                  <div key={poi.id} className="bg-white border border-gray-100 rounded-xl p-3 shadow-sm">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <div className="text-sm font-bold text-gray-800">{poi.name}</div>
                        <div className="text-[10px] text-gray-400 uppercase tracking-widest">
                          {getPriorityLabel(poi.priority)} · {formatDuration(poi.durationMins)}
                        </div>
                      </div>
                    </div>
                    <select
                      defaultValue=""
                      onChange={(e) => {
                        const value = Number(e.target.value);
                        if (!Number.isNaN(value)) {
                          moveUnscheduledToDay(poi.id, value);
                        }
                        e.target.value = "";
                      }}
                      className="mt-3 w-full rounded-lg border border-gray-200 px-3 py-2 text-xs font-bold text-gray-600"
                    >
                      <option value="" disabled>
                        Move to day...
                      </option>
                      {dayIndices.map((dayIndex) => (
                        <option key={dayIndex} value={dayIndex}>
                          Day {dayIndex + 1}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {dayIndices.map((dayIndex) => {
              const dayItems = tripState.days[dayIndex] || [];
              const dayDuration = dayItems.reduce((sum, item) => sum + item.durationMins, 0);
              return (
                <div key={`day-${dayIndex}`} className="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="text-sm font-black text-gray-800">Day {dayIndex + 1}</h4>
                      <span className="text-xs text-gray-400">{formatDuration(dayDuration)}</span>
                    </div>
                    {showOptimize && (
                      <button
                        type="button"
                        onClick={() => handleOptimizeDay(dayIndex)}
                        disabled={optimizingDayIndex === dayIndex}
                        className="px-3 py-2 rounded-lg bg-blue-50 text-blue-600 text-xs font-bold hover:bg-blue-600 hover:text-white transition disabled:opacity-60"
                      >
                        {optimizingDayIndex === dayIndex ? 'Optimizing...' : '✨ Optimize Route'}
                      </button>
                    )}
                  </div>
                  {optimizationErrors[dayIndex] && (
                    <div className="mb-3 text-xs text-red-500 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                      {optimizationErrors[dayIndex]}
                    </div>
                  )}
                  {dayItems.length === 0 ? (
                    <div className="text-xs text-gray-400 border border-dashed border-gray-200 rounded-lg px-3 py-4 text-center">
                      No items scheduled yet
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {dayItems.map((poi, poiIndex) => (
                        <div key={poi.id} className="border border-gray-100 rounded-xl p-3 bg-gray-50">
                          <div className="flex items-center justify-between gap-2">
                            <div>
                              <div className="text-sm font-bold text-gray-800">{poi.name}</div>
                              <div className="text-[10px] text-gray-400 uppercase tracking-widest">
                                {getPriorityLabel(poi.priority)} · {formatDuration(poi.durationMins)}
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-2 mt-3">
                            <button
                              type="button"
                              onClick={() => movePoiWithinDay(dayIndex, poiIndex, -1)}
                              className="px-3 py-1 rounded-lg border border-gray-200 text-xs font-bold text-gray-600 hover:bg-gray-100"
                            >
                              Up
                            </button>
                            <button
                              type="button"
                              onClick={() => movePoiWithinDay(dayIndex, poiIndex, 1)}
                              className="px-3 py-1 rounded-lg border border-gray-200 text-xs font-bold text-gray-600 hover:bg-gray-100"
                            >
                              Down
                            </button>
                            <button
                              type="button"
                              onClick={() => moveDayToUnscheduled(dayIndex, poiIndex)}
                              className="px-3 py-1 rounded-lg border border-red-100 text-xs font-bold text-red-500 hover:bg-red-50"
                            >
                              Remove
                            </button>
                          </div>
                          {dayIndices.length > 1 && (
                            <select
                              defaultValue=""
                              onChange={(e) => {
                                const value = Number(e.target.value);
                                if (!Number.isNaN(value)) {
                                  moveDayToDay(dayIndex, value, poiIndex);
                                }
                                e.target.value = "";
                              }}
                              className="mt-3 w-full rounded-lg border border-gray-200 px-3 py-2 text-xs font-bold text-gray-600"
                            >
                              <option value="" disabled>
                                Move to day...
                              </option>
                              {dayIndices.filter((idx) => idx !== dayIndex).map((idx) => (
                                <option key={idx} value={idx}>
                                  Day {idx + 1}
                                </option>
                              ))}
                            </select>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderStageFour = () => renderTimelineBoard(false);

  const renderStageFive = () => renderTimelineBoard(true);

  return (
    <PageTransition className="flex w-full h-full bg-gray-50/50 overflow-y-auto font-sans">
      <div className="max-w-6xl mx-auto w-full px-6 py-8 space-y-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-black text-gray-800">Itinerary Funnel</h1>
              <p className="text-sm text-gray-500 mt-1">
                Progressive planning for {session?.destination || 'your destination'}.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs font-bold text-gray-500">
              <Sparkles size={16} className="text-blue-500" />
              Funnel-to-Timeline Flow
            </div>
          </div>
          <div className="mt-6">{renderStageIndicator()}</div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          {currentStage === 1 && renderStageOne()}
          {currentStage === 2 && renderStageTwo()}
          {currentStage === 3 && renderStageThree()}
          {currentStage === 4 && renderStageFour()}
          {currentStage === 5 && renderStageFive()}
        </div>

        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setCurrentStage((prev) => Math.max(prev - 1, 1))}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-gray-200 text-gray-600 hover:bg-gray-50 font-bold text-sm transition"
            disabled={currentStage === 1}
          >
            <ArrowLeft size={16} />
            Back
          </button>

          <button
            type="button"
            onClick={() => setCurrentStage((prev) => Math.min(prev + 1, 5))}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-blue-100 bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white font-black text-sm transition"
            disabled={currentStage === 5}
          >
            Next
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </PageTransition>
  );
}

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
          {currentStage === 3 && (
            <div className="text-center py-12 text-gray-500">
              <h2 className="text-xl font-black text-gray-800">Allocator Coming Next</h2>
              <p className="text-sm mt-2">We will cluster your picks into day plans here.</p>
            </div>
          )}
          {currentStage === 4 && (
            <div className="text-center py-12 text-gray-500">
              <h2 className="text-xl font-black text-gray-800">Timeline Editor Coming Next</h2>
              <p className="text-sm mt-2">Drag, drop, and reorder your daily cards.</p>
            </div>
          )}
          {currentStage === 5 && (
            <div className="text-center py-12 text-gray-500">
              <h2 className="text-xl font-black text-gray-800">Daily Optimizer Coming Next</h2>
              <p className="text-sm mt-2">Optimize each day with a single click.</p>
            </div>
          )}
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

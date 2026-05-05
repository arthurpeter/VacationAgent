import React, { useState, useEffect } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import { MapPin, Bus, Car, Footprints, Loader2, ArrowRight, ArrowLeft, Settings2, Sparkles, Map } from 'lucide-react';

import { fetchWithAuth } from '../../authService'; 
import { API_BASE_URL } from '../../config';
import PageTransition from '../../components/PageTransition';

export default function ItineraryStage() {
  const { sessionData } = useOutletContext();
  const session = sessionData?.data || sessionData;
  const sessionId = session?.id;

  // --- UI PROGRESSION STATE ---
  const [currentStage, setCurrentStage] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);

  // --- GLOBAL TRIP STATE ---
  const [tripState, setTripState] = useState({
    preferences: {
      transitMode: "transit", // 'walk', 'drive', 'transit'
      pace: "balanced", // 'chill', 'balanced', 'packed'
    },
    // Dummy data so you can see the UI immediately
    unscheduled: [
      { id: 'poi_1', name: 'The Louvre', category: 'Museum', priority: null, durationMins: 180, image: '🏛️' },
      { id: 'poi_2', name: 'Eiffel Tower', category: 'Landmark', priority: null, durationMins: 120, image: '🗼' },
      { id: 'poi_3', name: 'Le Marais Food Tour', category: 'Food', priority: null, durationMins: 150, image: '🥐' },
      { id: 'poi_4', name: 'Catacombs', category: 'History', priority: null, durationMins: 90, image: '💀' },
      { id: 'poi_5', name: 'Seine River Cruise', category: 'Activity', priority: null, durationMins: 60, image: '⛵' },
    ],
    days: [] // Array of arrays: [ [poi_1, poi_2], [poi_3] ]
  });

  // --- HANDLERS ---
  const handleSetPriority = (poiId, priorityLevel) => {
    setTripState(prev => ({
      ...prev,
      unscheduled: prev.unscheduled.map(poi => 
        poi.id === poiId ? { ...poi, priority: priorityLevel } : poi
      )
    }));
  };

  const handleGenerateItinerary = async () => {
    setIsProcessing(true);
    // TODO: Connect to Python /itinerary/allocate endpoint here
    // For now, fake a 2-second API delay, then manually split the data
    setTimeout(() => {
      const selected = tripState.unscheduled.filter(p => p.priority !== null);
      setTripState(prev => ({
        ...prev,
        // Fake clustering: Put first 2 items in Day 1, rest in Day 2
        days: [ selected.slice(0, 2), selected.slice(2) ],
        unscheduled: prev.unscheduled.filter(p => p.priority === null)
      }));
      setIsProcessing(false);
      setCurrentStage(4); // Jump to Timeline Editor
    }, 2000);
  };

  // --- SUB-COMPONENTS (THE STAGES) ---

  const renderStage1_Bucket = () => (
    <div className="space-y-6 animate-fadeIn">
      <div className="mb-8 text-center max-w-2xl mx-auto">
        <h2 className="text-3xl font-black text-gray-900 mb-4">What sounds good?</h2>
        <p className="text-gray-500">Tag the places you'd like to visit. Don't worry about the schedule yet, we'll organize it for you later.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tripState.unscheduled.map(poi => (
          <div key={poi.id} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all">
            <div className="text-4xl mb-3">{poi.image}</div>
            <h3 className="font-bold text-gray-900 text-lg">{poi.name}</h3>
            <p className="text-sm text-gray-500 mb-4">{poi.category} • ~{poi.durationMins / 60} hrs</p>
            
            <div className="flex gap-2">
              <button 
                onClick={() => handleSetPriority(poi.id, 1)}
                className={`flex-1 py-2 text-xs font-bold rounded-xl border ${poi.priority === 1 ? 'bg-blue-600 text-white border-blue-600' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'}`}
              >
                🥇 Must Do
              </button>
              <button 
                onClick={() => handleSetPriority(poi.id, 2)}
                className={`flex-1 py-2 text-xs font-bold rounded-xl border ${poi.priority === 2 ? 'bg-green-600 text-white border-green-600' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'}`}
              >
                👍 Want To
              </button>
              <button 
                onClick={() => handleSetPriority(poi.id, 3)}
                className={`flex-1 py-2 text-xs font-bold rounded-xl border ${poi.priority === 3 ? 'bg-orange-500 text-white border-orange-500' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'}`}
              >
                🤷 If Time
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 flex justify-end">
        <button 
          onClick={() => setCurrentStage(2)}
          disabled={tripState.unscheduled.filter(p => p.priority).length === 0}
          className="flex items-center gap-2 bg-gray-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-gray-800 disabled:opacity-50 transition-all"
        >
          Next: Logistics <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );

  const renderStage2_Logistics = () => (
    <div className="max-w-2xl mx-auto space-y-8 animate-fadeIn">
      <div className="text-center mb-10">
        <h2 className="text-3xl font-black text-gray-900 mb-4">How are you getting around?</h2>
        <p className="text-gray-500">This helps us calculate accurate travel times between your stops.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { id: 'transit', icon: Bus, label: 'Public Transit', desc: 'Buses, trains, subways' },
          { id: 'walk', icon: Footprints, label: 'Walking', desc: 'I want to stay local' },
          { id: 'drive', icon: Car, label: 'Driving', desc: 'Rental car or rideshares' }
        ].map(mode => (
          <button
            key={mode.id}
            onClick={() => setTripState(prev => ({ ...prev, preferences: { ...prev.preferences, transitMode: mode.id } }))}
            className={`p-6 rounded-2xl border-2 text-left transition-all ${tripState.preferences.transitMode === mode.id ? 'border-blue-600 bg-blue-50' : 'border-gray-200 bg-white hover:border-blue-300'}`}
          >
            <mode.icon size={32} className={`mb-4 ${tripState.preferences.transitMode === mode.id ? 'text-blue-600' : 'text-gray-400'}`} />
            <h3 className="font-bold text-gray-900">{mode.label}</h3>
            <p className="text-xs text-gray-500 mt-1">{mode.desc}</p>
          </button>
        ))}
      </div>

      <div className="flex justify-between pt-10">
        <button onClick={() => setCurrentStage(1)} className="flex items-center gap-2 text-gray-500 hover:text-gray-900 font-bold px-4 py-3">
          <ArrowLeft size={18} /> Back
        </button>
        <button 
          onClick={handleGenerateItinerary}
          className="flex items-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-700 transition-all shadow-md hover:shadow-lg"
        >
          {isProcessing ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
          Generate Magic Route
        </button>
      </div>
    </div>
  );

  const renderStage4_Editor = () => (
    <div className="flex flex-col lg:flex-row gap-8 h-full animate-fadeIn">
      {/* Left Column: Parking Lot */}
      <div className="w-full lg:w-1/3 bg-gray-50 rounded-2xl p-5 border border-gray-200 flex flex-col">
        <h3 className="font-black text-gray-900 mb-4 flex items-center gap-2"><Map size={18}/> Parking Lot</h3>
        <p className="text-xs text-gray-500 mb-4">Items that didn't fit, or that you un-scheduled.</p>
        <div className="space-y-3 overflow-y-auto flex-1">
          {tripState.unscheduled.map(poi => (
            <div key={poi.id} className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm opacity-70">
              <span className="text-2xl mr-2">{poi.image}</span>
              <span className="font-bold text-sm text-gray-800">{poi.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right Column: The Timeline */}
      <div className="w-full lg:w-2/3 space-y-8">
        <div className="flex justify-between items-center bg-white p-5 rounded-2xl border border-gray-200 shadow-sm">
           <div>
             <h2 className="text-xl font-black text-gray-900">Your Structured Trip</h2>
             <p className="text-sm text-gray-500">Drag to reorder, or click optimize to let us do the math.</p>
           </div>
        </div>

        {tripState.days.map((day, index) => (
          <div key={index} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="bg-blue-50/50 px-5 py-3 border-b border-gray-100 flex justify-between items-center">
              <h3 className="font-black text-gray-800">Day {index + 1}</h3>
              <button className="text-xs font-bold text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-blue-200 hover:bg-blue-600 hover:text-white transition-colors">
                ✨ Route this Day
              </button>
            </div>
            <div className="p-5 space-y-3">
              {day.map((poi, pIdx) => (
                <div key={poi.id} className="flex items-center gap-4 bg-gray-50 p-4 rounded-xl border border-gray-100">
                  <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center font-bold text-sm text-gray-400 border border-gray-200 shadow-sm">
                    {pIdx + 1}
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900">{poi.name}</h4>
                    <p className="text-xs text-gray-500">Stay: ~{poi.durationMins / 60} hrs</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <PageTransition className="w-full h-full overflow-y-auto bg-white p-4 md:p-8">
      {/* Progress Bar Header */}
      <div className="max-w-4xl mx-auto mb-10 flex items-center justify-between border-b border-gray-100 pb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black">
            {currentStage}
          </div>
          <div>
            <h1 className="font-black text-gray-900 text-lg">Itinerary Builder</h1>
            <p className="text-xs font-medium text-gray-500">
              {currentStage === 1 && "Select objectives"}
              {currentStage === 2 && "Configure logistics"}
              {currentStage >= 3 && "Review & Route"}
            </p>
          </div>
        </div>
      </div>

      {/* Render the active stage */}
      <div className="max-w-5xl mx-auto pb-20">
        {currentStage === 1 && renderStage1_Bucket()}
        {currentStage === 2 && renderStage2_Logistics()}
        {currentStage === 4 && renderStage4_Editor()}
      </div>
    </PageTransition>
  );
}
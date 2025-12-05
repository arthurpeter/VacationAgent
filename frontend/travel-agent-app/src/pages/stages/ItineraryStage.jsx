import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';

export default function ItineraryStage() {
  const { sessionData } = useOutletContext();
  const [itinerary, setItinerary] = useState(null);
  const [generating, setGenerating] = useState(false);

  // Load existing itinerary from DB
  useEffect(() => {
    if (sessionData?.data?.itinerary) {
      setItinerary(sessionData.data.itinerary);
    }
  }, [sessionData]);

  const handleGenerate = () => {
    setGenerating(true);
    // TODO: Call backend to generate itinerary
    setTimeout(() => {
        setItinerary(MOCK_ITINERARY);
        setGenerating(false);
    }, 2000);
  };

  // State 1: No Itinerary yet (Prompt to Generate)
  if (!itinerary && !generating) {
    return (
        <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-gray-50">
            <div className="bg-white p-10 rounded-3xl shadow-sm border border-gray-100 max-w-lg">
                <span className="text-4xl mb-4 block">🗓️</span>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Build Your Day-by-Day Plan</h2>
                <p className="text-gray-500 mb-8">
                    We have your flight and hotel details. Let our AI craft a personalized schedule 
                    filled with activities, restaurants, and hidden gems.
                </p>
                <button 
                    onClick={handleGenerate}
                    className="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-700 transition shadow-lg hover:shadow-xl"
                >
                    Generate Itinerary
                </button>
            </div>
        </div>
    );
  }

  // State 2: Generating
  if (generating) {
      return (
        <div className="flex flex-col items-center justify-center h-full bg-gray-50">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600 font-medium">Crafting your perfect schedule...</p>
        </div>
      );
  }

  // State 3: Display Itinerary
  return (
    <div className="w-full h-full bg-gray-50 overflow-y-auto p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
            <div>
                <h1 className="text-3xl font-extrabold text-gray-900">Your Itinerary</h1>
                <p className="text-sm text-gray-500">2 Travelers • Paris, France</p>
            </div>
            <div className="flex gap-3">
                <button className="px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 font-medium text-sm transition">
                    Export PDF
                </button>
                <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium text-sm transition shadow-md">
                    Finish & Save
                </button>
            </div>
        </div>

        <div className="space-y-6 pb-20">
            {itinerary.days.map((day, index) => (
                <DayCard key={index} dayNumber={index + 1} dayData={day} />
            ))}
        </div>
      </div>
    </div>
  );
}

// --- Sub-components ---

function DayCard({ dayNumber, dayData }) {
    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="bg-gradient-to-r from-blue-50 to-white p-4 border-b border-gray-100 flex justify-between items-center">
                <h3 className="font-bold text-lg text-blue-900">Day {dayNumber}</h3>
                <span className="text-xs font-bold text-blue-600 bg-blue-100 px-3 py-1 rounded-full uppercase tracking-wide">
                    {dayData.theme}
                </span>
            </div>
            <div className="p-4 divide-y divide-gray-50">
                {dayData.activities.map((activity, idx) => (
                    <div key={idx} className="py-4 flex gap-4 first:pt-0 last:pb-0 group">
                        <div className="flex flex-col items-center min-w-[60px]">
                            <span className="text-xs font-bold text-gray-400 group-hover:text-blue-500 transition">{activity.time}</span>
                            <div className="h-full w-px bg-gray-100 mt-2"></div>
                        </div>
                        <div className="flex-grow">
                            <h4 className="font-bold text-gray-800">{activity.title}</h4>
                            <p className="text-sm text-gray-500 mt-1 leading-relaxed">{activity.description}</p>
                            {activity.location && (
                                <div className="mt-2 text-xs text-gray-400 font-medium flex items-center gap-1">
                                    📍 {activity.location}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

// --- Mock Data ---
const MOCK_ITINERARY = {
    days: [
        {
            theme: "Arrival & Exploration",
            activities: [
                { time: "10:00 AM", title: "Land at CDG Airport", description: "Take the RER B train to the city center." },
                { time: "01:00 PM", title: "Check-in at Hotel Le A", description: "Drop off bags and freshen up." },
                { time: "03:00 PM", title: "Walk along the Seine", location: "Quai de la Tournelle", description: "Enjoy the views of Notre Dame and browsing the bookstalls." },
                { time: "07:30 PM", title: "Dinner at Le Relais de l'Entrecôte", location: "Saint-Germain", description: "Famous steak frites restaurant." }
            ]
        },
        {
            theme: "Art & Culture",
            activities: [
                { time: "09:30 AM", title: "Louvre Museum Tour", location: "Rue de Rivoli", description: "Guided tour focusing on the Renaissance wing." },
                { time: "01:00 PM", title: "Lunch at Tuileries Gardens", description: "Quick bite at a cafe in the park." },
                { time: "03:00 PM", title: "Shopping in Le Marais", description: "Explore vintage shops and boutiques." }
            ]
        }
    ]
};
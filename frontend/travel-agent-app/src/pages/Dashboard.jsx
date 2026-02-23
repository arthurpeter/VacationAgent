import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; 
import VacationCard from '../components/VacationCard';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';

export default function Dashboard() {
  const [vacations, setVacations] = useState([]);
  const navigate = useNavigate();

  // 1. Helper to fetch a single session's details (used for resume)
  const getSession = async (sessionId) => {
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/session/${sessionId}`, {}, "GET");
      if (res && res.ok) {
        return await res.json();
      }
    } catch (error) {
      console.error("Error fetching session details:", error);
    }
    return null;
  };

  // 2. Load all sessions on mount
  useEffect(() => {
    const loadSessions = async () => {
        try {
            const res = await fetchWithAuth(`${API_BASE_URL}/session/getSessions`, {}, "GET");
            if (res.ok) {
                const data = await res.json();
                const ids = data.session_ids || [];

                // Fetch details for each ID in parallel
                const sessionPromises = ids.map(id => 
                    fetchWithAuth(`${API_BASE_URL}/session/${id}`, {}, "GET")
                        .then(r => r.json())
                );
                
                const sessionsDetails = await Promise.all(sessionPromises);
                
                // Format for the UI
                const formattedSessions = sessionsDetails.map(s => ({
                    id: s.id, 
                    destination: s.destination || "New Trip",
                    // Map backend "current_stage" to a number for the UI if needed, or pass string
                    stage: s.current_stage || 'discovery', 
                    current_stage: s.current_stage || 'discovery',
                    description: s.session_data?.summary || `Created on ${new Date(s.created_at).toLocaleDateString()}`,
                    date: new Date(s.updated_at || s.created_at).toLocaleDateString(),
                    budget: s.session_data?.budget 
                }));

                setVacations(formattedSessions);
            }
        } catch (err) {
            console.error("Failed to load sessions", err);
        }
    };
    loadSessions();
  }, []);

  // 3. Smart Resume Handler: Redirects to the correct stage
  const handleResumeSession = async (sessionId) => {
    // Optimistic check from local state first
    const session = vacations.find(v => v.id === sessionId);
    let stage = session?.current_stage;

    // If missing, fetch fresh data
    if (!stage) {
        const freshData = await getSession(sessionId);
        stage = freshData?.current_stage;
    }

    // Default to discovery
    let targetRoute = 'discovery'; 
    
    // Map backend stage to frontend route
    if (stage) {
        const stageMap = {
            'discovery': 'discovery',
            'options': 'options',
            'itinerary': 'itinerary',
            'booking': 'booking',
            'completed': 'itinerary' 
        };
        targetRoute = stageMap[stage] || 'discovery';
    }

    navigate(`/plan/${sessionId}/${targetRoute}`);
  };

  // 4. Create New Session Handler
  const handleCreateNew = async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/session/create`, {}, "POST");
      
      if (res && res.ok) {
        const data = await res.json();
        // New sessions always start at discovery
        navigate(`/plan/${data.session_id}/discovery`);
      } else {
        console.error("Failed to create session");
      }
    } catch (err) {
      console.error("Error creating session:", err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 px-8 py-12">
      <div className="max-w-6xl mx-auto">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">Your Trips</h1>
            <p className="text-gray-500 mt-1">Manage your ongoing plans and past adventures.</p>
          </div>
          <button 
            onClick={handleCreateNew}
            className="mt-4 md:mt-0 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg transition transform hover:-translate-y-0.5"
          >
            + Create New Vacation
          </button>
        </div>

        {/* Empty State */}
        {vacations.length === 0 && (
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-3xl p-10 text-white text-center shadow-xl mb-12">
            <h2 className="text-3xl font-bold mb-4">Ready for your next adventure?</h2>
            <p className="text-blue-100 mb-8 max-w-xl mx-auto">Start a conversation with our AI agent to build your perfect itinerary from scratch.</p>
            <button 
              onClick={handleCreateNew}
              className="px-8 py-3 bg-white text-blue-600 font-bold rounded-xl shadow hover:bg-gray-100 transition"
            >
              Start Planning Now
            </button>
          </div>
        )}

        {/* History Grid */}
        {vacations.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* "Plan a New Trip" Card */}
            <div 
              onClick={handleCreateNew}
              className="group border-2 border-dashed border-gray-300 rounded-2xl p-6 flex flex-col items-center justify-center text-center hover:border-blue-500 hover:bg-blue-50 transition min-h-[200px] cursor-pointer"
            >
              <div className="h-12 w-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <span className="text-2xl font-bold">+</span>
              </div>
              <h3 className="text-lg font-bold text-gray-700 group-hover:text-blue-700">Plan a New Trip</h3>
              <p className="text-sm text-gray-400 mt-2">Start from scratch</p>
            </div>

            {/* Vacation Cards */}
            {vacations.map(vacation => (
              // We wrap the card in a div to capture the click and handle the resume logic
              <div key={vacation.id} onClick={() => handleResumeSession(vacation.id)} className="cursor-pointer">
                 <VacationCard vacation={vacation} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
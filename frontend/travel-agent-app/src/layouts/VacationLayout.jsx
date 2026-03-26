import React, { useEffect, useState } from 'react';
import { Outlet, NavLink, useParams, useLocation } from 'react-router-dom';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';

const getStageFromPath = (pathname) => {
  if (pathname.includes('/discovery')) return 'discovery';
  if (pathname.includes('/options')) return 'options';
  if (pathname.includes('/itinerary')) return 'itinerary';
  if (pathname.includes('/booking')) return 'booking';
  return null; 
};

const updateSessionStage = async (sessionId, stage) => {
  try {
    await fetchWithAuth(`${API_BASE_URL}/session/${sessionId}/stage`, {
      stage: stage 
    }, "PATCH");
  } catch (error) {
    console.error("Failed to auto-save stage:", error);
  }
};

export default function VacationLayout() {
  const { id } = useParams(); // The vacation/session ID
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  // This function allows child components to refresh the shared state
  const refreshContext = async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/session/${id}`, {}, "GET");
      if (res.ok) {
        const data = await res.json();
        setSessionData(data);
      }
    } catch (error) {
      console.error("Failed to load session context", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshContext();
  }, [id]);

  useEffect(() => {
    const stage = getStageFromPath(location.pathname);
    if (stage && id) {
      updateSessionStage(id, stage);
    }
  }, [location.pathname, id]);

  if (loading) return <div className="p-10 text-center">Loading your trip...</div>;

  // FIX: Create a unified session variable that handles both nested and unnested API responses
  const session = sessionData?.data || sessionData;

  return (
    <div className="flex flex-col h-screen bg-gray-50 font-sans">
      {/* 1. Persistent Top Bar */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center shrink-0">
        
        {/* LEFT SIDE: Given flex-1 so it takes equal space as the right side */}
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-800 line-clamp-1 pr-4">
            {session?.destination || "New Vacation Plan"}
          </h1>
          <p className="text-xs text-gray-500">ID: {id}</p>
        </div>
        
        {/* CENTER: The 3-Stage Stepper Navigation */}
        <nav className="flex bg-gray-100 p-1 rounded-lg shrink-0">
          <StageLink to="discovery" label="1. Discovery" />
          <StageLink to="options" label="2. Options" />
          <StageLink to="itinerary" label="3. Itinerary" />
        </nav>

        {/* RIGHT SIDE: Also given flex-1 to perfectly balance the left side */}
        <div className="flex-1 flex flex-col justify-center items-end pl-4">
            {session?.budget ? (
              <>
                <span className="text-xs text-gray-400 uppercase font-bold tracking-wider mb-0.5">Target Budget</span>
                <span className="text-lg font-black text-green-600 leading-none">
                  {session.budget.toLocaleString()} <span className="text-sm">{session.currency || ''}</span>
                </span>
              </>
            ) : (
              <span className="text-sm font-semibold text-gray-400 border border-gray-200 px-3 py-1 rounded-full">
                No Budget Set
              </span>
            )}
        </div>
        
      </header>

      {/* 2. Main Stage Area */}
      <main className="flex-grow overflow-hidden flex">
        {/* Pass sessionData and refresh function to children via Outlet context */}
        <Outlet context={{ sessionData, refreshContext }} />
      </main>
    </div>
  );
}

// Helper for the navigation tabs
function StageLink({ to, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-4 py-2 text-sm font-medium rounded-md transition ${
          isActive
            ? "bg-white text-blue-600 shadow-sm"
            : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
        }`
      }
    >
      {label}
    </NavLink>
  );
}
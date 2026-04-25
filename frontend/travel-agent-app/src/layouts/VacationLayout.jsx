import React, { useEffect, useState } from 'react';
import { Outlet, NavLink, useParams, useLocation, useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';
import { toast, Toaster } from 'react-hot-toast';

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
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFinalizing, setIsFinalizing] = useState(false);

  const refreshContext = async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/session/${id}`, {}, "GET");
      if (res && res.ok) {
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

  useEffect(() => {
    const timer = setTimeout(() => {
      window.scrollTo({ top: 76, behavior: 'smooth' });
    }, 100);
    return () => clearTimeout(timer);
  }, [location.pathname]);

  if (loading) return <div className="p-10 text-center">Loading your trip...</div>;

  const session = sessionData?.data || sessionData;

  const canFinalize = session && (
    session.flights_url || 
    session.accomodation_url || 
    session.itinerary_text || 
    (session.extra_links && session.extra_links.length > 0)
  );

  const handleFinalizeTrip = async () => {
    if (!session) return;
    setIsFinalizing(true);
    
    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/session/finalize/${id}`, 
        {}, 
        "POST"
      );
      
      if (response && response.ok) {
        if (session.is_active) {
          toast.success(
            "Plan finished! ✈️ Generating email... we'll notify you when it's ready.",
            { duration: 4000 } 
          );
          refreshContext();
        } else {
          toast.success(
            "Email queued! ✈️ We'll notify you once it has been dispatched.",
            { duration: 4000 }
          );
        }
      } else {
        toast.error("Something went wrong. Please try again.");
      }
    } catch (error) {
      console.error(error);
      toast.error("Failed to connect to the server.");
    } finally {
      setIsFinalizing(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 font-sans">
      <Toaster position="top-center" reverseOrder={false} />
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center shrink-0">

        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-800 line-clamp-1 pr-4">
            {session?.destination || "New Vacation Plan"}
          </h1>
          <p className="text-xs text-gray-500 flex items-center gap-2 mt-0.5">
            <span>ID: {id}</span>
            {session && !session.is_active && (
              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px] font-bold uppercase tracking-wider">
                Completed
              </span>
            )}
          </p>
        </div>

        <nav className="flex bg-gray-100 p-1 rounded-lg shrink-0">
          <StageLink to="discovery" label="1. Discovery" />
          <StageLink to="options" label="2. Options" />
          <StageLink to="itinerary" label="3. Itinerary" />
        </nav>

        <div className="flex-1 flex justify-end items-center gap-6 pl-4">
          <div className="flex flex-col items-end">
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

          {canFinalize && (
            <button 
              onClick={handleFinalizeTrip} 
              disabled={isFinalizing}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-bold transition-all ${
                isFinalizing 
                  ? 'bg-gray-200 cursor-not-allowed text-gray-500 shadow-none' 
                  : session.is_active
                    ? 'bg-gray-900 hover:bg-gray-800 text-white shadow-md hover:-translate-y-0.5' 
                    : 'bg-white border-2 border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50' 
              }`}
            >
              {isFinalizing ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-sm">Processing...</span>
                </>
              ) : session.is_active ? (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  <span className="text-sm">Finish Plan</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                  </svg>
                  <span className="text-sm">Resend Email</span>
                </>
              )}
            </button>
          )}
        </div>
        
      </header>

      <main className="flex-grow overflow-hidden flex">
        <Outlet context={{ sessionData, refreshContext }} />
      </main>
    </div>
  );
}

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
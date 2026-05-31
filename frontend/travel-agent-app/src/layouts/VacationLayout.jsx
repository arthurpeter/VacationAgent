import React, { useEffect, useState } from 'react';
import { Outlet, NavLink, useParams, useLocation, useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';
import { toast, Toaster } from 'react-hot-toast';

const getStageFromPath = (pathname) => {
  if (pathname.includes('/discovery')) return 'discovery';
  if (pathname.includes('/options')) return 'options';
  if (pathname.includes('/itinerary')) return 'itinerary';
  if (pathname.includes('/overview')) return 'booking'; // 1. Map overview sub-route to backend booking state
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
        toast.success("Plan finished! ✈️ Generating email... we'll notify you when it's ready.", { duration: 4000 });
        await refreshContext();
        navigate('/dashboard'); // Take them back to dashboard after a successful finish
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

        {/* 2. Added Step 4 Overview directly to the layout navigation */}
        <nav className="flex bg-gray-100 p-1 rounded-lg shrink-0">
          <StageLink to="discovery" label="1. Discovery" />
          <StageLink to="options" label="2. Options" />
          <StageLink to="itinerary" label="3. Itinerary" />
          <StageLink to="overview" label="4. Overview" />
        </nav>

        {/* 3. Completely removed the finalize button from the right header actions */}
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
        </div>
        
      </header>

      <main className="flex-grow overflow-hidden flex">
        {/* 4. FIXED: Kept sessionData EXACTLY as it was to prevent sibling page crashes, simply adding handlers down the line */}
        <Outlet context={{ sessionData, refreshContext, handleFinalizeTrip, isFinalizing }} />
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
            ? "bg-white text-blue-600 shadow-sm font-bold"
            : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
        }`
      }
    >
      {label}
    </NavLink>
  );
}
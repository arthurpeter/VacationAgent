import React, { useEffect, useState } from 'react';
import { Outlet, NavLink, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../authService';

export default function VacationLayout() {
  const { id } = useParams(); // The vacation/session ID
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);

  // This function allows child components to refresh the shared state
  const refreshContext = async () => {
    try {
      const res = await fetchWithAuth(`http://localhost:5000/vacations/session/${id}`, {}, "GET");
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

  if (loading) return <div className="p-10 text-center">Loading your trip...</div>;

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 1. Persistent Top Bar */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-800">
            {sessionData?.data?.destination || "New Vacation Plan"}
          </h1>
          <p className="text-xs text-gray-500">ID: {id}</p>
        </div>
        
        {/* The 3-Stage Stepper Navigation */}
        <nav className="flex bg-gray-100 p-1 rounded-lg">
          <StageLink to="discovery" label="1. Discovery" />
          <StageLink to="options" label="2. Options" />
          <StageLink to="itinerary" label="3. Itinerary" />
        </nav>

        <div className="w-32 text-right">
            {/* Save/Exit buttons could go here */}
            <span className="text-sm font-semibold text-green-600">
                {sessionData?.data?.budget ? `Budget: $${sessionData.data.budget}` : 'No Budget Set'}
            </span>
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
            : "text-gray-500 hover:text-gray-700"
        }`
      }
    >
      {label}
    </NavLink>
  );
}
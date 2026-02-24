import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
// 1. Import the logo image
import logo from '../assets/logo.png'; 

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuth();
  
  // State for toggling the notifications dropdown
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const handleLogout = () => {
    logout();
    navigate("/"); // Safely redirect to the root (which handles unauthenticated users)
  };

  return (
    <nav className="flex items-center justify-between px-8 py-4 bg-white shadow-sm border-b border-gray-100">
      
      {/* Brand / Logo */}
      <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition">
        <img 
          src={logo} 
          alt="VacationAgent Logo" 
          className="h-10 w-auto object-contain" 
        />
      </Link>

      {/* Navigation */}
      <div className="flex items-center gap-6">
        {isAuthenticated ? (
          <>
            {/* Primary Navigation Links */}
            <Link 
              to="/" 
              className={`font-medium transition ${location.pathname === "/" ? "text-blue-600" : "text-gray-500 hover:text-gray-900"}`}
            >
              Dashboard
            </Link>
            <Link 
              to="/history" 
              className={`font-medium transition ${location.pathname === "/history" ? "text-blue-600" : "text-gray-500 hover:text-gray-900"}`}
            >
              History
            </Link>
            <Link 
              to="/help" 
              className={`font-medium transition ${location.pathname === "/help" ? "text-blue-600" : "text-gray-500 hover:text-gray-900"}`}
            >
              Help
            </Link>

            {/* Vertical Divider */}
            <div className="h-6 w-px bg-gray-200 mx-1"></div>

            {/* Notifications Bell */}
            <div className="relative flex items-center">
              <button 
                onClick={() => {
                  setShowNotifications(!showNotifications);
                  if (!showNotifications) setUnreadCount(0); // Optional: clear notifications when opened
                }}
                className="text-gray-500 hover:text-blue-600 focus:outline-none transition relative"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                
                {/* ONLY render the red dot if unreadCount is greater than 0 */}
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 block h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white"></span>
                )}
              </button>

              {/* Notifications Dropdown Panel */}
              {showNotifications && (
                <div className="absolute right-0 top-10 mt-2 w-72 bg-white rounded-xl shadow-lg border border-gray-100 z-50 overflow-hidden">
                  <div className="p-3 border-b bg-gray-50 flex justify-between items-center">
                    <span className="text-sm font-semibold text-gray-800">Notifications</span>
                    <button className="text-xs text-blue-600 hover:underline">Mark read</button>
                  </div>
                  
                  {/* Empty State / Future Integration Point */}
                  <div className="p-6 text-center text-sm text-gray-500">
                    {/* =============================================================
                      TODO: INTEGRATE REAL-TIME NOTIFICATIONS
                      =============================================================
                      For a complete product, replace this static message by mapping 
                      over a `notifications` state array. 
                      
                      Backend Integration Options:
                      1. Polling: setInterval to fetch `/api/notifications` every X mins.
                      2. WebSockets: Connect to FastAPI websockets for live pushes.
                      3. Webhooks: If you use an external service for price drops, 
                         have it ping your backend, which then pushes via SSE 
                         (Server-Sent Events) to this React component.
                      =============================================================
                    */}
                    <p>No new notifications right now.</p>
                  </div>
                  
                </div>
              )}
            </div>

            {/* Profile Avatar wrapped in a Link */}
            <Link to="/profile" className="flex items-center hover:opacity-80 transition group">
              <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs border border-blue-200 group-hover:bg-blue-200 group-hover:border-blue-300 transition">
                ME
              </div>
            </Link>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="text-gray-500 hover:text-red-600 font-medium transition text-sm ml-2"
            >
              Sign Out
            </button>
          </>
        ) : (
          /* Unauthenticated State */
          <>
            <Link to="/login" className="text-gray-600 hover:text-blue-600 font-medium transition">
              Login
            </Link>
            <Link to="/register" className="px-5 py-2.5 rounded-xl bg-gray-900 text-white font-semibold hover:bg-gray-800 transition shadow-lg shadow-gray-200">
              Get Started
            </Link>
          </>
        )}
      </div>
      
    </nav>
  );
}
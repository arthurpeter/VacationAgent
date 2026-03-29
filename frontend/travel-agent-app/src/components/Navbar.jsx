import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { fetchWithAuth } from "../authService";
import { API_BASE_URL } from "../config";
import logo from '../assets/logo.png'; 

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuth();
  
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  useEffect(() => {
    if (!isAuthenticated) return;
    
    let isMounted = true;

    const startNotificationStream = async () => {
      try {
        const res = await fetchWithAuth(`${API_BASE_URL}/notifications/stream`, null, "GET");

        if (!res || !res.body) return;

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (isMounted) {
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop();

          for (const part of parts) {
            if (part.startsWith('data: ')) {
              const dataStr = part.replace('data: ', '');
              try {
                const parsedData = JSON.parse(dataStr);
                setNotifications(parsedData);
                setUnreadCount(parsedData.filter(n => !n.is_read).length);
              } catch (e) {
                console.error("Failed to parse notification JSON:", e);
              }
            }
          }
        }
      } catch (error) {
        console.error("Notification stream error:", error);
      }
    };

    startNotificationStream();

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated]);

  const handleMarkAllRead = async () => {
    if (unreadCount === 0) return;
    
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    setUnreadCount(0);

    await fetchWithAuth(`${API_BASE_URL}/notifications/read`, {}, "PATCH");
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    
    const updatedNotifs = notifications.filter(n => n.id !== id);
    setNotifications(updatedNotifs);
    setUnreadCount(updatedNotifs.filter(n => !n.is_read).length);

    await fetchWithAuth(`${API_BASE_URL}/notifications/${id}`, {}, "DELETE");
  };

  const formatTime = (isoString) => {
    if (!isoString) return "";
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <nav className="flex items-center justify-between px-8 py-4 bg-white shadow-sm border-b border-gray-100">
      
      {/* Brand / Logo */}
      <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition">
        <img src={logo} alt="VacationAgent Logo" className="h-10 w-auto object-contain" />
      </Link>

      {/* Navigation */}
      <div className="flex items-center gap-6">
        {isAuthenticated ? (
          <>
            <Link to="/" className={`font-medium transition ${location.pathname === "/" ? "text-blue-600" : "text-gray-500 hover:text-gray-900"}`}>
              Dashboard
            </Link>
            <Link to="/history" className={`font-medium transition ${location.pathname === "/history" ? "text-blue-600" : "text-gray-500 hover:text-gray-900"}`}>
              History
            </Link>
            <Link to="/help" className={`font-medium transition ${location.pathname === "/help" ? "text-blue-600" : "text-gray-500 hover:text-gray-900"}`}>
              Help
            </Link>

            <div className="h-6 w-px bg-gray-200 mx-1"></div>

            {/* Notifications Bell */}
            <div className="relative flex items-center">
              <button 
                onClick={() => {
                  const newState = !showNotifications;
                  setShowNotifications(newState);
                  if (newState && unreadCount > 0) {
                    handleMarkAllRead();
                  }
                }}
                className="text-gray-500 hover:text-blue-600 focus:outline-none transition relative"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 block h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white"></span>
                )}
              </button>

              {/* Notifications Dropdown Panel */}
              {showNotifications && (
                <div className="absolute right-0 top-10 mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-100 z-50 overflow-hidden flex flex-col max-h-96">
                  <div className="p-3 border-b bg-gray-50 flex justify-between items-center shrink-0">
                    <span className="text-sm font-semibold text-gray-800">Notifications</span>
                    {unreadCount > 0 && (
                      <button onClick={handleMarkAllRead} className="text-xs text-blue-600 hover:underline">
                        Mark all read
                      </button>
                    )}
                  </div>
                  
                  <div className="overflow-y-auto flex-1">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-sm text-gray-500">
                        <p>No notifications right now. 🌴</p>
                      </div>
                    ) : (
                      <ul className="divide-y divide-gray-50">
                        {notifications.map((notif) => (
                          <li 
                            key={notif.id} 
                            className={`p-4 hover:bg-gray-50 transition relative group ${notif.is_read ? 'bg-white text-gray-600' : 'bg-blue-50/50 text-gray-900'}`}
                          >
                            <div className="flex justify-between items-start pr-6">
                              <p className="text-sm leading-snug">{notif.message}</p>
                              {/* Delete Button (Visible on Hover) */}
                              <button 
                                onClick={(e) => handleDelete(e, notif.id)}
                                className="absolute right-3 top-4 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition"
                                title="Delete notification"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                              </button>
                            </div>
                            <span className="text-xs text-gray-400 mt-2 block">
                              {formatTime(notif.created_at)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Profile Avatar & Logout */}
            <Link to="/profile" className="flex items-center hover:opacity-80 transition group ml-2">
              <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs border border-blue-200 group-hover:bg-blue-200 group-hover:border-blue-300 transition">
                ME
              </div>
            </Link>
            <button onClick={handleLogout} className="text-gray-500 hover:text-red-600 font-medium transition text-sm ml-2">
              Sign Out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="text-gray-600 hover:text-blue-600 font-medium transition">Login</Link>
            <Link to="/register" className="px-5 py-2.5 rounded-xl bg-gray-900 text-white font-semibold hover:bg-gray-800 transition shadow-lg shadow-gray-200">
              Get Started
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
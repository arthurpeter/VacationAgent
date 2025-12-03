import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
// 1. Import the logo image
import logo from '../assets/logo.png'; // Make sure the filename matches!

export default function Navbar() {
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  return (
    <nav className="flex items-center justify-between px-8 py-4 bg-white shadow-sm border-b border-gray-100">
      {/* Brand / Logo */}
      <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition">
        <img 
          src={logo} 
          alt="TuRAG Logo" 
          className="h-10 w-auto object-contain" 
        />
      </Link>

      {/* Navigation */}
      <div className="flex items-center gap-6">
        {isAuthenticated ? (
          <>
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
            <div className="h-6 w-px bg-gray-200 mx-2"></div>
            <button
              onClick={logout}
              className="text-gray-500 hover:text-red-600 font-medium transition text-sm"
            >
              Sign Out
            </button>
            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs border border-blue-200">
              ME
            </div>
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
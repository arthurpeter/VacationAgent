import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Navbar() {
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  // Map routes to titles
  const pageTitles = {
    "/":  isAuthenticated ? "Chat" : "Home",
    "/login": "Login",
    "/register": "Register",
  };

  const currentPage = pageTitles[location.pathname] || "";

  return (
    <nav className="flex items-center justify-between px-8 py-4 bg-white shadow-md">
      {/* Left side: Current page title */}
      <div className="text-2xl font-extrabold text-blue-600 tracking-tight">
        {currentPage}
      </div>

      {/* Right side: Navigation links */}
      <div className="flex items-center gap-6">
        <Link
          to="/"
          className={`font-medium transition ${
            location.pathname === "/"
              ? "text-blue-600"
              : "text-gray-700 hover:text-blue-600"
          }`}
        >
          {isAuthenticated ? "Chat" : "Home"}
        </Link>
        {isAuthenticated ? (
          // If the user is authenticated, show a Logout button
          <button
            onClick={logout}
            className="px-4 py-2 rounded-xl bg-red-500 text-white font-semibold hover:bg-red-600 transition shadow"
          >
            Logout
          </button>
        ) : (
          // If the user is not authenticated, show Login and Register links
          <>
            <Link
              to="/login"
              className={`font-medium transition ${
                location.pathname === "/login"
                  ? "text-blue-600"
                  : "text-gray-700 hover:text-blue-600"
              }`}
            >
              Login
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition shadow"
            >
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}

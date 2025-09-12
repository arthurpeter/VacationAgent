import React, { createContext, useState, useContext, useEffect } from 'react';
import { getAccessToken, clearTokens, setTokens, fetchWithAuth, getCSRFToken } from '../authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true); // To handle initial auth check

  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken();
      if (token) {
        const res = await fetchWithAuth("http://localhost:5000/auth/validate", {}, "POST");
        if (res.ok) {
          setIsAuthenticated(true);
        }
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  const login = (accessToken) => {
    setTokens(accessToken);
    setIsAuthenticated(true);
  };

  const logout = async () => {
    const csrfToken = getCSRFToken();
    console.log("CSRF Token from cookie:", csrfToken);
    
    const headers = {
      "Authorization": `Bearer ${getAccessToken()}`,
      "Content-Type": "application/json"
    };
    
    // Add CSRF token header if available
    if (csrfToken) {
      headers["X-CSRF-TOKEN-Refresh"] = csrfToken;
      console.log("Adding CSRF token to header:", csrfToken);
    }
    
    console.log("Logout headers:", headers);
    
    const res = await fetch("http://localhost:5000/auth/logout", {
      method: "POST",
      headers,
      credentials: "include",
    });
    
    if (!res.ok) {
      console.error("Failed to logout from server");
    }
    
    clearTokens();
    setIsAuthenticated(false);
    window.location.href = '/login';
  };

  // Don't render the app until the initial authentication check is complete
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-lg font-medium text-gray-900 mb-2">Loading Application</h2>
          <p className="text-sm text-gray-600">Initializing authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to easily use the auth context
export const useAuth = () => useContext(AuthContext);
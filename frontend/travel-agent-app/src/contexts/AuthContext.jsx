import React, { createContext, useState, useContext, useEffect } from 'react';
import { getAccessToken, clearTokens, setTokens, fetchWithAuth } from '../authService';

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
    const res = await fetch("http://localhost:5000/auth/logout", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${getAccessToken()}`
      },
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
    return <div>Loading...</div>; // Or a spinner component
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to easily use the auth context
export const useAuth = () => useContext(AuthContext);
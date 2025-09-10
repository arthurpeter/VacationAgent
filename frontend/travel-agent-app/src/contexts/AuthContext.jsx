import React, { createContext, useState, useContext, useEffect } from 'react';
import { getAccessToken, clearTokens, setTokens } from '../authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true); // To handle initial auth check

  useEffect(() => {
    const checkAuth = async () => {
      const token = getAccessToken();
      if (token) {
        // Here you would ideally validate the token with a lightweight backend request
        // For now, we'll assume if a token exists, the user is authenticated.
        // The fetchWithAuth service will handle expired tokens automatically.
        setIsAuthenticated(true);
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  const login = (accessToken, refreshToken) => {
    setTokens(accessToken, refreshToken);
    setIsAuthenticated(true);
  };

  const logout = () => {
    clearTokens();
    setIsAuthenticated(false);
    window.location.href = '/login'; // Redirect to login on logout
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
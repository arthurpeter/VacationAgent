import React, { createContext, useState, useContext, useEffect } from 'react';
import { getAccessToken, clearTokens, setTokens, fetchWithAuth, getCSRFToken } from '../authService';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE_URL } from '../config';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = getAccessToken();
        if (token) {
          const res = await fetchWithAuth(`${API_BASE_URL}/auth/validate`, {}, "POST");
          if (res && res.ok) {
            setIsAuthenticated(true);
          } else {
            clearTokens();
            setIsAuthenticated(false);
          }
        }
      } catch (err) {
        console.error("Auth check error:", err);
        clearTokens();
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
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

    if (csrfToken) {
      headers["X-CSRF-TOKEN-Refresh"] = csrfToken;
      console.log("Adding CSRF token to header:", csrfToken);
    }
    
    console.log("Logout headers:", headers);
    
    const res = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      headers,
      credentials: "include",
    });
    
    if (!res.ok) {
      console.error("Failed to logout from server");
    }
    
    clearTokens();
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div 
            key="app-loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="flex flex-col items-center justify-center min-h-screen bg-gray-50 absolute inset-0 z-50"
          >
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h2 className="text-lg font-medium text-gray-900 mb-2">Loading Application</h2>
              <p className="text-sm text-gray-600">Checking Credentials...</p>
            </div>
          </motion.div>
        ) : (
          <motion.div 
            key="app-content"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="w-full h-full"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
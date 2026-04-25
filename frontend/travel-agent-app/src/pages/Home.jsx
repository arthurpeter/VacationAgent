import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import LandingPage from './LandingPage';
import Dashboard from './Dashboard';

export default function Home() {
  const { isAuthenticated } = useAuth();

  return isAuthenticated ? <Dashboard /> : <LandingPage />;
}

import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import LandingPage from './LandingPage';
import Chat from './Chat';

export default function Home() {
  const { isAuthenticated } = useAuth();

  // If the user is authenticated, show the chat. Otherwise, show the public landing page.
  return isAuthenticated ? <Chat /> : <LandingPage />;
}

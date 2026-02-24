import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-9xl font-extrabold text-blue-600">404</h1>
        <h2 className="text-3xl font-bold text-gray-900 mt-4">Lost Luggage? Or just a lost page?</h2>
        <p className="text-gray-500 mt-4 mb-8 max-w-md mx-auto">
          We can't seem to find the page you're looking for. The AI might be scouting new destinations, but let's get you back to familiar territory.
        </p>
        <Link 
          to="/" 
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import VacationCard from '../components/VacationCard';

const MOCK_HISTORY = [
  { id: '1', destination: 'Paris, France', step: 2, description: 'Romantic getaway for 2, budget 3000€', date: '2 mins ago' },
  { id: '2', destination: 'Tokyo, Japan', step: 1, description: 'Adventure trip seeking anime spots', date: '2 days ago' },
  { id: '3', destination: 'Bali, Indonesia', step: 4, description: 'Relaxing beach vacation', date: '1 month ago' },
];

export default function Dashboard() {
  const [vacations, setVacations] = useState(MOCK_HISTORY);

  return (
    <div className="min-h-screen bg-gray-50 px-8 py-12">
      <div className="max-w-6xl mx-auto">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">Your Trips</h1>
            <p className="text-gray-500 mt-1">Manage your ongoing plans and past adventures.</p>
          </div>
          <Link to="/chat/new">
            <button className="mt-4 md:mt-0 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg transition transform hover:-translate-y-0.5">
              + Create New Vacation
            </button>
          </Link>
        </div>

        {vacations.length === 0 && (
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-3xl p-10 text-white text-center shadow-xl mb-12">
            <h2 className="text-3xl font-bold mb-4">Ready for your next adventure?</h2>
            <p className="text-blue-100 mb-8 max-w-xl mx-auto">Start a conversation with our AI agent to build your perfect itinerary from scratch.</p>
            <Link to="/chat/new">
              <button className="px-8 py-3 bg-white text-blue-600 font-bold rounded-xl shadow hover:bg-gray-100 transition">
                Start Planning Now
              </button>
            </Link>
          </div>
        )}

        {/* History Grid */}
        {vacations.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Link to="/chat/new" className="group border-2 border-dashed border-gray-300 rounded-2xl p-6 flex flex-col items-center justify-center text-center hover:border-blue-500 hover:bg-blue-50 transition min-h-[200px]">
              <div className="h-12 w-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition">
                <span className="text-2xl font-bold">+</span>
              </div>
              <h3 className="text-lg font-bold text-gray-700 group-hover:text-blue-700">Plan a New Trip</h3>
              <p className="text-sm text-gray-400 mt-2">Start from scratch</p>
            </Link>

            {/* Map through history */}
            {vacations.map(vacation => (
              <VacationCard key={vacation.id} vacation={vacation} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
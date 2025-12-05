import React from 'react';
import { Link } from 'react-router-dom';

const STEP_LABELS = {
  1: "Discovery (Chat)",
  2: "Options Selection",
  3: "Itinerary Finalization",
  4: "Completed"
};

const STEP_COLORS = {
  1: "bg-blue-100 text-blue-800",
  2: "bg-purple-100 text-purple-800",
  3: "bg-orange-100 text-orange-800",
  4: "bg-green-100 text-green-800"
};

export default function VacationCard({ vacation }) {
  const isCompleted = vacation.step === 4;
  
  return (
    <div className="bg-white rounded-2xl shadow-sm hover:shadow-md transition border border-gray-100 overflow-hidden flex flex-col">
      <div className={`h-2 w-full ${isCompleted ? 'bg-green-500' : 'bg-blue-500'}`}></div>
      <div className="p-6 flex-grow flex flex-col">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xl font-bold text-gray-900 line-clamp-1">{vacation.destination || "New Trip"}</h3>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${STEP_COLORS[vacation.step]}`}>
            {STEP_LABELS[vacation.step]}
          </span>
        </div>
        
        <p className="text-gray-500 text-sm mb-6 flex-grow line-clamp-2">
          {vacation.description || "No details yet..."}
        </p>

        <div className="flex items-center justify-between mt-auto">
          <span className="text-xs text-gray-400">Last updated: {vacation.date}</span>
          <Link 
            to={`/plan/${vacation.id}`}
            className="px-4 py-2 bg-gray-50 text-blue-600 font-semibold rounded-lg hover:bg-blue-50 transition text-sm"
          >
            {isCompleted ? "View Summary" : "Continue Planning →"}
          </Link>
        </div>
      </div>
    </div>
  );
}
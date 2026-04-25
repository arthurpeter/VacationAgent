import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';


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

export default function VacationCard({ vacation, onDelete }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const isCompleted = vacation.step === 4;

  const handleDelete = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const confirmed = window.confirm("Are you sure you want to delete this trip? This action cannot be undone.");
    if (!confirmed) return;

    setIsDeleting(true);
    try {
      const response = await fetchWithAuth(
        `${API_BASE_URL}/session/${vacation.id}`,
        {}, 
        "DELETE"
      );

      if (response && response.ok) {
        if (onDelete) onDelete(vacation.id);
        toast.success("Trip deleted successfully.");
      } else {
        const errorData = await response?.json();
        toast.error(`Deletion failed: ${errorData?.detail || "Unknown server error"}`);
      }
    } catch (err) {
      console.error("Delete request error:", err);
      toast.error("A network error occurred while trying to delete the trip.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="group relative bg-white rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 border border-gray-100 overflow-hidden flex flex-col h-full">

      <div className={`h-1.5 w-full ${isCompleted ? 'bg-green-500' : 'bg-blue-500'}`}></div>

      <button
        onClick={handleDelete}
        disabled={isDeleting}
        className="absolute top-3 right-3 z-20 p-2 bg-white/90 backdrop-blur-sm text-red-500 rounded-full 
                   opacity-0 group-hover:opacity-100 hover:bg-red-500 hover:text-white 
                   transition-all duration-200 border border-red-100 shadow-sm disabled:cursor-not-allowed"
        title="Delete Trip"
      >
        {isDeleting ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        )}
      </button>

      <div className="p-6 flex-grow flex flex-col">
        <div className="flex justify-between items-start mb-4 pr-6">
          <h3 className="text-xl font-bold text-gray-900 line-clamp-1">
            {vacation.destination || "Unnamed Trip"}
          </h3>
          <span className={`px-2.5 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-bold whitespace-nowrap ${STEP_COLORS[vacation.step]}`}>
            {STEP_LABELS[vacation.step]}
          </span>
        </div>
        
        <p className="text-gray-500 text-sm mb-6 flex-grow line-clamp-2 leading-relaxed">
          {vacation.description || "No specific details added yet for this trip..."}
        </p>

        <div className="flex items-center justify-between mt-auto pt-4 border-t border-gray-50">
          <div className="flex flex-col">
            <span className="text-[10px] text-gray-400 uppercase font-semibold">Last updated</span>
            <span className="text-xs text-gray-600 font-medium">{vacation.date || "N/A"}</span>
          </div>
          
          <Link 
            to={`/plan/${vacation.id}`}
            className={`px-4 py-2 text-sm font-bold rounded-xl transition-colors ${
              isCompleted 
                ? "bg-green-50 text-green-700 hover:bg-green-100" 
                : "bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
            }`}
          >
            {isCompleted ? "View Summary" : "Continue Plan"}
          </Link>
        </div>
      </div>
    </div>
  );
}
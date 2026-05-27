import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Plane, Hotel, Calendar, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';

export default function OverviewStage() {
  // Pulling the layout context placeholders (ready for when we wire it up)
  const { session, handleFinalizeTrip, isFinalizing } = useOutletContext();

  // Temporary mock data for visual drafting
  const mockSummary = {
    destination: session?.destination || "Rome, Italy",
    dates: "Feb 18, 2026 - Feb 25, 2026",
    travelers: "2 Adults",
    flight: {
      airline: "ITA Airways",
      time: "09:30 AM - 11:45 AM",
      price: "240 EUR",
    },
    hotel: {
      name: "c-hotels Club House Roma",
      address: "Via Andrea Alciato 14, Rome",
      price: "469 EUR",
    }
  };

  return (
    <div className="flex-grow overflow-y-auto bg-gray-50 p-6 md:p-8 custom-scrollbar">
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        
        {/* HEADER SUMMARY CARD */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm flex flex-wrap justify-between items-center gap-4">
          <div>
            <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md">
              Reviewing Trip Draft
            </span>
            <h2 className="text-3xl font-black text-gray-900 mt-2">{mockSummary.destination}</h2>
            <p className="text-xs text-gray-400 font-medium mt-1">{mockSummary.dates} • {mockSummary.travelers}</p>
          </div>
          <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-xl border border-emerald-100">
            <CheckCircle size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">All Steps Secured</span>
          </div>
        </div>

        {/* LOGISTICS SNAPSHOT GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Flight Placeholder */}
          <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-xs font-black uppercase tracking-wider text-gray-400 mb-1">Transit Choice</h4>
                <div className="text-base font-black text-gray-800">{mockSummary.flight.airline}</div>
                <p className="text-xs text-gray-500 mt-1">{mockSummary.flight.time}</p>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
                <Plane size={20} />
              </div>
            </div>
            <div className="text-right border-t border-gray-50 pt-4 mt-4 font-black text-sm text-blue-600">
              {mockSummary.flight.price}
            </div>
          </div>

          {/* Accommodation Placeholder */}
          <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
            <div className="flex justify-between items-start">
              <div>
                <h4 className="text-xs font-black uppercase tracking-wider text-gray-400 mb-1">Stay Lodging</h4>
                <div className="text-base font-black text-gray-800 truncate max-w-[240px]" title={mockSummary.hotel.name}>
                  {mockSummary.hotel.name}
                </div>
                <p className="text-xs text-gray-500 mt-1 truncate max-w-[240px]">{mockSummary.hotel.address}</p>
              </div>
              <div className="p-3 bg-green-50 text-green-600 rounded-2xl">
                <Hotel size={20} />
              </div>
            </div>
            <div className="text-right border-t border-gray-50 pt-4 mt-4 font-black text-sm text-green-600">
              {mockSummary.hotel.price}
            </div>
          </div>
        </div>

        {/* TIMELINE PREVIEW PLACEHOLDER */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm">
          <h3 className="text-lg font-black text-gray-900 mb-4 flex items-center gap-2">
            <Calendar size={18} className="text-gray-400" /> Route Timeline Manifest
          </h3>
          <div className="border-l-2 border-gray-100 ml-3 pl-6 py-2 space-y-4 opacity-50 select-none">
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">[ Schedule details render blueprint container here ]</div>
            <div className="w-full bg-gray-100 h-10 rounded-xl" />
            <div className="w-4/5 bg-gray-100 h-10 rounded-xl" />
          </div>
        </div>

        {/* BOTTOM GATE CONTROLS */}
        <div className="bg-white border border-amber-200 bg-gradient-to-r from-white to-amber-50/20 rounded-3xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl mt-0.5 border border-amber-100">
              <AlertTriangle size={16} />
            </div>
            <div>
              <h4 className="font-black text-gray-900 text-sm">Lock in Itinerary & Dispatch Documentation</h4>
              <p className="text-xs text-gray-400 mt-0.5 font-medium">
                Confirming generates the system tracking rows, archives the metrics, and triggers your document compilation.
              </p>
            </div>
          </div>
          
          <button
            type="button"
            onClick={handleFinalizeTrip}
            disabled={isFinalizing}
            className="w-full sm:w-auto bg-gray-900 hover:bg-gray-800 disabled:bg-gray-200 text-white font-black text-xs uppercase tracking-widest px-6 py-3.5 rounded-xl transition-all shadow-md flex items-center justify-center gap-2 group shrink-0"
          >
            <span>{isFinalizing ? "Compiling..." : "Finalize & Email"}</span>
            <ArrowRight size={14} className="transform transition-transform group-hover:translate-x-0.5" />
          </button>
        </div>

      </div>
    </div>
  );
}
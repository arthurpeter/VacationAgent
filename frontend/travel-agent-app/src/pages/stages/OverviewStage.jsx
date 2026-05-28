import React, { useEffect, useState } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import { 
  Plane, 
  Hotel, 
  Calendar, 
  AlertTriangle, 
  CheckCircle, 
  ArrowRight, 
  Loader2, 
  Car, 
  TrainFront, 
  MapPin 
} from 'lucide-react';
import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';

export default function OverviewStage() {
  const { id } = useParams();
  
  // Pull core state context values safely from your VacationLayout
  const { sessionData, handleFinalizeTrip, isFinalizing } = useOutletContext();
  const session = sessionData?.data || sessionData;

  const [compiledItinerary, setCompiledItinerary] = useState(null);
  const [isCompiling, setIsCompiling] = useState(true);

  // Trigger compiler logic on initial stage mount
  useEffect(() => {
    const runCompilationPass = async () => {
      try {
        setIsCompiling(true);
        const res = await fetchWithAuth(`${API_BASE_URL}/session/compile/${id}`, {}, "POST");
        if (res && res.ok) {
          const data = await res.json();
          setCompiledItinerary(data.itinerary_data);
        }
      } catch (error) {
        console.error("Failed to run monolithic compilation pass:", error);
      } finally {
        setIsCompiling(false);
      }
    };

    if (id) {
      runCompilationPass();
    }
  }, [id]);

  // Loading Screen Wrapper
  if (isCompiling) {
    return (
      <div className="flex-grow flex flex-col items-center justify-center bg-gray-50 h-full">
        <Loader2 className="animate-spin text-blue-600 mb-4" size={40} />
        <h3 className="font-black text-lg text-gray-900">Assembling Final Overview Manifest</h3>
        <p className="text-xs text-gray-400 mt-1">Parsing optimized time windows and mapping mobility layers...</p>
      </div>
    );
  }

  // Format Dates safely for layout display
  const formatDate = (dateString) => {
    if (!dateString) return "TBD";
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const mobility = compiledItinerary?.mobility;
  const timeline = compiledItinerary?.timeline || [];

  return (
    <div className="flex-grow overflow-y-auto bg-gray-50 p-6 md:p-8 custom-scrollbar">
      <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
        
        {/* HEADER SUMMARY CARD */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm flex flex-wrap justify-between items-center gap-4">
          <div>
            <span className="text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-2.5 py-1 rounded-md">
              Reviewing Final Itinerary Manifest
            </span>
            <h2 className="text-3xl font-black text-gray-900 mt-2">
              {session?.destination || "Your Custom Vacation"}
            </h2>
            <p className="text-xs text-gray-400 font-medium mt-1">
              {formatDate(session?.from_date)} - {formatDate(session?.to_date)} • {session?.adults || 1} Adults {session?.children > 0 ? `• ${session.children} Children` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-xl border border-emerald-100">
            <CheckCircle size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Draft Compiled</span>
          </div>
        </div>

        {/* LOGISTICS SNAPSHOT GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Flight Card Block */}
          <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
            <div className="flex justify-between items-start gap-2">
              <div className="min-w-0">
                <h4 className="text-xs font-black uppercase tracking-wider text-gray-400 mb-1">Transit Channel</h4>
                <div className="text-base font-black text-gray-800 truncate">
                  {session?.airport_name || "No Flight Selected"}
                </div>
                {session?.flights_url && (
                  <a href={session.flights_url} target="_blank" rel="noreferrer" className="text-[11px] text-blue-500 font-bold hover:underline block mt-1">
                    View Flight Link ➔
                  </a>
                )}
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl shrink-0">
                <Plane size={20} />
              </div>
            </div>
            <div className="text-right border-t border-gray-50 pt-4 mt-4 font-black text-sm text-blue-600">
              {session?.flight_price ? `${session.flight_price} ${session.flight_ccy || 'EUR'}` : "---"}
            </div>
          </div>

          {/* Accommodation Card Block */}
          <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
            <div className="flex justify-between items-start gap-2">
              <div className="min-w-0">
                <h4 className="text-xs font-black uppercase tracking-wider text-gray-400 mb-1">Stay Lodging</h4>
                <div className="text-base font-black text-gray-800 truncate" title={session?.accommodation_name}>
                  {session?.accommodation_name || "No Hotel Selected"}
                </div>
                <p className="text-xs text-gray-500 mt-1 truncate" title={session?.accommodation_address}>
                  {session?.accommodation_address || "Address unavailable"}
                </p>
              </div>
              <div className="p-3 bg-green-50 text-green-600 rounded-2xl shrink-0">
                <Hotel size={20} />
              </div>
            </div>
            <div className="text-right border-t border-gray-50 pt-4 mt-4 font-black text-sm text-green-600">
              {session?.accommodation_price ? `${session.accommodation_price} ${session.accommodation_ccy || 'EUR'}` : "---"}
            </div>
          </div>

          {/* Unified Mobility Card Block */}
          <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
            <div className="flex justify-between items-start gap-2">
              <div className="min-w-0">
                <h4 className="text-xs font-black uppercase tracking-wider text-gray-400 mb-1">Ground Strategy</h4>
                <div className="text-base font-black text-gray-800">
                  {mobility?.has_rental_car ? "Rental Car Active" : "Public Transport"}
                </div>
                {mobility?.official_link && (
                  <a href={mobility.official_link} target="_blank" rel="noreferrer" className="text-[11px] text-purple-500 font-bold hover:underline block mt-1">
                    Official Transit Info ➔
                  </a>
                )}
              </div>
              <div className={`p-3 rounded-2xl shrink-0 ${mobility?.has_rental_car ? 'bg-orange-50 text-orange-600' : 'bg-purple-50 text-purple-600'}`}>
                {mobility?.has_rental_car ? <Car size={20} /> : <TrainFront size={20} />}
              </div>
            </div>
            <div className="text-right border-t border-gray-50 pt-4 mt-4 font-black text-sm text-gray-800">
              {mobility?.price_est ? `${mobility.price_est} ${mobility.currency || 'EUR'}` : "Free Strategy"}
            </div>
          </div>
        </div>

        {/* TIME-LINE MANIFEST LIST CONTAINER */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm space-y-6">
          <h3 className="text-lg font-black text-gray-900 flex items-center gap-2">
            <Calendar size={18} className="text-gray-400" /> Confirmed Route Timeline
          </h3>

          {timeline.length === 0 ? (
            <div className="text-center py-6 text-gray-400 text-sm border-2 border-dashed rounded-2xl">
              No daily schedule events built for this itinerary layer.
            </div>
          ) : (
            <div className="space-y-8 pl-2">
              {timeline.map((day) => (
                <div key={day.day_index} className="relative border-l-2 border-gray-100 pl-6 space-y-4">
                  {/* Floating Day Indicator Node */}
                  <div className="absolute -left-[11px] top-0 bg-gray-900 text-white text-[10px] font-black w-5 h-5 rounded-full flex items-center justify-center shadow-sm">
                    {day.day_index + 1}
                  </div>
                  
                  <h4 className="text-sm font-black text-gray-800 uppercase tracking-wider">
                    Day {day.day_index + 1} ({formatDate(day.date)})
                  </h4>

                  <div className="space-y-3">
                    {day.events?.map((event, eventIdx) => (
                      <div key={event.id || eventIdx} className="bg-gray-50 border border-gray-100 rounded-2xl p-4 flex justify-between items-center gap-4">
                        <div className="min-w-0">
                          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">
                            {event.start_time} - {event.end_time}
                          </span>
                          <h5 className="font-black text-gray-800 text-sm truncate mt-0.5">{event.name}</h5>
                          {event.formatted_address && (
                            <p className="text-xs text-gray-400 truncate mt-0.5 flex items-center gap-1">
                              <MapPin size={11} className="shrink-0" /> {event.formatted_address}
                            </p>
                          )}
                        </div>

                        {/* Inline short transit metadata summary indicator */}
                        {event.transit_path && (
                          <div className="shrink-0 text-right bg-white px-3 py-1.5 rounded-xl border border-gray-100 text-[10px] font-bold text-gray-500 flex items-center gap-1">
                            {event.transit_path.mode === 'uber' || event.transit_path.mode === 'driving' ? <Car size={11} /> : <TrainFront size={11} />}
                            <span>{event.transit_path.duration_mins}m</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
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
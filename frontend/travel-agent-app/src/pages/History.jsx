import React, { useEffect, useState } from 'react';
import { Calendar, MapPin, Plane, Building, ArrowRight, Trash2, ArrowLeft, ExternalLink, Users } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { toast, Toaster } from 'react-hot-toast';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';
import PageTransition from '../components/PageTransition';

export default function History() {
  const [vacations, setVacations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedVacation, setSelectedVacation] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const calculateDays = (start, end) => {
    if (!start || !end || start === "TBD" || end === "TBD") return "?";
    const diffTime = Math.abs(new Date(end) - new Date(start));
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  };

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/history/vacations`, {}, "GET");
      if (res.ok) {
        const data = await res.json();
        setVacations(data);
      }
    } catch (err) {
      console.error("Failed to load history:", err);
      toast.error("Failed to load your travel history.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDetails = async (tripId) => {
    const loadingToast = toast.loading("Unpacking blueprint...");
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/history/vacations/${tripId}`, {}, "GET");
      if (res.ok) {
        const fullData = await res.json();
        setSelectedVacation(fullData);
        toast.dismiss(loadingToast);
      } else {
        toast.error("Failed to load details.", { id: loadingToast });
      }
    } catch (err) {
      console.error(err);
      toast.error("Error loading blueprint.", { id: loadingToast });
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation(); 
    
    const isConfirmed = window.confirm(
      "Are you sure you want to delete this trip blueprint? This action is permanent and cannot be undone."
    );
    
    if (!isConfirmed) return;

    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/history/vacations/${id}`, {}, "DELETE");
      if (res.ok) {
        toast.success("Trip deleted permanently.");
        setVacations(prev => prev.filter(v => v.id !== id));
        if (selectedVacation?.id === id) setSelectedVacation(null);
      } else {
        toast.error("Failed to delete the trip.");
      }
    } catch (err) {
      console.error(err);
      toast.error("An error occurred while deleting.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-50">
        <div className="animate-pulse text-blue-600 font-medium text-lg">Loading your passports...</div>
      </div>
    );
  }

  if (selectedVacation) {
    const vac = selectedVacation;
    const days = vac.itinerary_data || [];

    return (
      <PageTransition className="min-h-screen bg-gray-50 p-6 md:p-10 font-sans pb-20">
        <Toaster position="top-center" />
        <div className="max-w-4xl mx-auto">
          
          <button 
            onClick={() => setSelectedVacation(null)}
            className="flex items-center gap-2 text-gray-500 hover:text-blue-600 font-bold mb-6 transition-colors"
          >
            <ArrowLeft size={18} /> Back to Passport
          </button>

          <div className="bg-slate-900 rounded-3xl p-8 md:p-10 text-white shadow-xl mb-8 relative overflow-hidden">
            <div className="relative z-10">
              <h1 className="text-3xl md:text-5xl font-black mb-4">{vac.destination}</h1>
              <p className="text-slate-300 flex flex-wrap items-center gap-x-6 gap-y-3 font-medium text-sm md:text-base">
                <span className="flex items-center gap-2"><MapPin size={18}/> From {vac.origin || "Home"}</span>
                <span className="flex items-center gap-2"><Calendar size={18}/> {vac.from_date} - {vac.to_date}</span>
                {vac.people_count && <span className="flex items-center gap-2"><Users size={18}/> {vac.people_count} Travelers</span>}
              </p>
            </div>
            <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-white/5 rounded-full blur-3xl"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {vac.flight_price && (
              <div className="bg-white border-l-4 border-blue-500 rounded-2xl p-6 shadow-sm">
                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1 flex items-center gap-2">
                  <Plane size={16} className="text-blue-500" /> Estimated Flights
                </h4>
                <p className="text-3xl font-black text-gray-800">
                  {vac.flight_price} <span className="text-lg font-bold text-gray-400">{vac.flight_ccy}</span>
                </p>
              </div>
            )}
            {vac.accomodation_price && (
              <div className="bg-white border-l-4 border-emerald-500 rounded-2xl p-6 shadow-sm">
                <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1 flex items-center gap-2">
                  <Building size={16} className="text-emerald-500" /> Estimated Hotel
                </h4>
                <p className="text-3xl font-black text-gray-800">
                  {vac.accomodation_price} <span className="text-lg font-bold text-gray-400">{vac.accomodation_ccy}</span>
                </p>
              </div>
            )}
          </div>

          {vac.transit_strategy && Object.keys(vac.transit_strategy).length > 0 && (
            <div className="bg-blue-50 border border-blue-100 rounded-2xl p-8 mb-8 shadow-sm">
              <h4 className="text-[10px] font-black tracking-widest text-blue-600 uppercase mb-2">Local Transit Strategy</h4>
              <h3 className="text-2xl font-black text-gray-900 mb-2">
                {vac.transit_strategy.pass_name} <span className="text-gray-500 font-medium">— {vac.transit_strategy.price}</span>
              </h3>
              <p className="text-gray-600 text-sm leading-relaxed mb-5 max-w-2xl">{vac.transit_strategy.description}</p>
              {vac.transit_strategy.purchase_url && (
                <a href={vac.transit_strategy.purchase_url} target="_blank" rel="noopener noreferrer" className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-6 rounded-xl text-sm transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5">
                  Get Official Pass
                </a>
              )}
            </div>
          )}

          {days.length > 0 && (
            <div>
              <h3 className="text-2xl font-black text-slate-800 mb-6 border-b border-slate-200 pb-4">Daily Itinerary</h3>
              <div className="space-y-6">
                {days.map((day, idx) => (
                  <div key={idx} className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="bg-slate-50 border-b border-slate-100 px-8 py-5">
                      <h4 className="text-xl font-black text-slate-800 flex items-center gap-3">
                        <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-100 text-blue-700 text-sm font-black shadow-sm shrink-0">
                          {day.day}
                        </span>
                        {day.title || `Day ${day.day}`}
                      </h4>
                    </div>
                    <div className="p-8">
                      <div className="prose prose-sm max-w-none text-slate-600 [&>p]:mb-4 last:[&>p]:mb-0 [&>strong]:text-slate-900 leading-relaxed">
                        <ReactMarkdown>{day.description}</ReactMarkdown>
                      </div>
                      
                      {day.links && day.links.length > 0 && (
                        <div className="mt-8 pt-6 border-t border-slate-100 flex flex-wrap gap-2">
                          {day.links.map((link, lIdx) => (
                            <a key={lIdx} href={link.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 px-3 py-2 bg-blue-50 border border-blue-100 text-blue-700 hover:bg-blue-600 hover:text-white rounded-lg text-xs font-bold transition-colors">
                              <ExternalLink size={14} /> {link.name}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="min-h-screen bg-gray-50 p-8 md:p-12 font-sans">
      <Toaster position="top-center" />
      <div className="max-w-6xl mx-auto">
        
        <header className="mb-10">
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Travel Passport</h1>
          <p className="text-gray-500 mt-2 font-medium">A history of all your finalized trip blueprints.</p>
        </header>

        {vacations.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-3xl border border-gray-200 shadow-sm">
            <MapPin className="mx-auto text-gray-300 mb-4" size={48} />
            <h3 className="text-xl font-bold text-gray-700">No trips yet</h3>
            <p className="text-gray-500 mt-2">Finish your first trip to see it saved here.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {vacations.map((trip) => {
               const daysCount = calculateDays(trip.from_date, trip.to_date);
               
               return (
                <div 
                  key={trip.id} 
                  onClick={() => handleViewDetails(trip.id)}
                  className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer group overflow-hidden flex flex-col relative"
                >
                  <button 
                    onClick={(e) => handleDelete(trip.id, e)}
                    className="absolute top-4 right-4 z-20 p-2.5 bg-black/30 hover:bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all backdrop-blur-md shadow-lg"
                    title="Delete Trip Permanently"
                  >
                    <Trash2 size={16} />
                  </button>

                  <div className="bg-slate-800 p-6 text-white relative overflow-hidden transition-colors group-hover:bg-slate-900">
                    <div className="relative z-10 pr-8">
                      <h2 className="text-2xl font-black mb-1 line-clamp-1">{trip.destination}</h2>
                      <p className="text-slate-300 text-sm flex items-center gap-1.5 font-medium">
                        <MapPin size={14} /> From {trip.origin || "Home"}
                      </p>
                    </div>
                    <div className="absolute -right-6 -top-6 w-24 h-24 bg-white/10 rounded-full blur-xl group-hover:scale-150 transition-transform duration-700 ease-out"></div>
                  </div>

                  <div className="p-6 flex-1 flex flex-col gap-5">
                    <div className="flex items-center justify-center gap-3 text-gray-600 text-sm font-bold bg-slate-50 px-3 py-2.5 rounded-xl border border-slate-100">
                      <Calendar size={16} className="text-blue-500" />
                      {trip.from_date} <ArrowRight size={12} className="text-gray-300 mx-1" /> {trip.to_date}
                    </div>

                    <div className="flex gap-4">
                      <div className={`flex-1 flex flex-col items-center justify-center gap-1 p-3 rounded-xl border ${trip.flight_price ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-gray-100 bg-gray-50 text-gray-400 opacity-50'} text-xs font-bold`}>
                        <Plane size={18} /> 
                        {trip.flight_price ? `${trip.flight_price} ${trip.flight_ccy}` : 'No Flights'}
                      </div>
                      <div className={`flex-1 flex flex-col items-center justify-center gap-1 p-3 rounded-xl border ${trip.accomodation_price ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-gray-100 bg-gray-50 text-gray-400 opacity-50'} text-xs font-bold`}>
                        <Building size={18} />
                        {trip.accomodation_price ? `${trip.accomodation_price} ${trip.accomodation_ccy}` : 'No Hotel'}
                      </div>
                    </div>
                  </div>

                  <div className="px-6 py-4 border-t border-gray-100 bg-gray-50 flex justify-between items-center group-hover:bg-blue-50 transition-colors">
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black text-gray-400 group-hover:text-blue-400 uppercase tracking-widest transition-colors">
                        {daysCount} Days Planned
                      </span>
                      {trip.created_at && (
                        <span className="text-[9px] font-bold text-gray-400 mt-0.5">
                          Saved {new Date(trip.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </span>
                      )}
                    </div>
                    
                    <span className="text-blue-600 font-bold text-sm flex items-center gap-1 group-hover:text-blue-800 transition-colors">
                      View Details <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </PageTransition>
  );
}
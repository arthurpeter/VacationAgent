import React, { useEffect, useState } from 'react';
import { 
  Calendar, 
  MapPin, 
  Plane, 
  Building, 
  ArrowRight, 
  Trash2, 
  ArrowLeft, 
  ExternalLink, 
  Users,
  Clock,
  AlertTriangle,
  ChevronDown,
  Compass,
  Hotel,
  Car,
  TrainFront
} from 'lucide-react';
import { toast, Toaster } from 'react-hot-toast';
import { fetchWithAuth } from '../authService';
import { API_BASE_URL } from '../config';
import PageTransition from '../components/PageTransition';

/* ─────────────────────────────────────────
   SHARED DESIGN SYSTEM INLINE STYLE BLOCK
───────────────────────────────────────── */
const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@300;400;500;700;900&display=swap');

  .ov-root * { box-sizing: border-box; }

  .ov-root {
    font-family: 'Inter', sans-serif;
    color: #0F172A;
    padding-top: 1rem;
  }

  .ov-sheet {
    max-width: 820px;
    margin: 0 auto;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
  }

  /* ── MASTHEAD ── */
  .ov-masthead {
    background: #0F172A;
    color: #FFFFFF;
    padding: 3rem 3rem 2.5rem;
    position: relative;
    overflow: hidden;
  }

  .ov-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #38BDF8;
    margin-bottom: 0.6rem;
    font-weight: 500;
  }

  .ov-destination {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin: 0 0 0.5rem;
  }

  .ov-dates {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #94A3B8;
    letter-spacing: 0.02em;
    margin-bottom: 2rem;
  }

  .ov-masthead-meta {
    display: flex;
    gap: 2.5rem;
    flex-wrap: wrap;
    border-top: 1px solid #1E293B;
    padding-top: 1.5rem;
  }

  .ov-meta-item { display: flex; flex-direction: column; gap: 4px; }
  .ov-meta-label {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #64748B;
  }
  .ov-meta-value { font-size: 13px; font-weight: 500; color: #E2E8F0; }

  /* ── BODY SECTIONS ── */
  .ov-body { padding: 0 3rem 3rem; }
  .ov-section { padding-top: 3rem; }

  .ov-section-rule {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .ov-section-num {
    font-size: 11px;
    font-weight: 900;
    color: #38BDF8;
    letter-spacing: 0.1em;
    flex-shrink: 0;
  }

  .ov-section-title {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #64748B;
    flex-shrink: 0;
    font-weight: 500;
  }

  .ov-rule { flex: 1; height: 1px; background: #F1F5F9; }

  /* ── LOGISTICS STRIP ── */
  .ov-logistics-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    background: transparent;
  }

  .ov-logistics-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .ov-lc-type {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748B;
    font-weight: 500;
    margin-bottom: 2px;
  }

  .ov-lc-name {
    font-size: 14px;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .ov-lc-sub {
    font-size: 11px;
    color: #64748B;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .ov-lc-price {
    font-family: 'DM Mono', monospace;
    font-size: 15px;
    font-weight: 700;
    color: #0EA5E9;
    margin-top: auto;
    padding-top: 8px;
  }

  .ov-lc-link {
    font-size: 10px;
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    margin-top: 4px;
  }
  .ov-lc-link:hover { text-decoration: underline; }

  /* ── DAY BLOCKS ── */
  .ov-day { margin-bottom: 3rem; }

  .ov-day-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #F1F5F9;
  }

  .ov-day-num {
    font-size: 22px;
    font-weight: 900;
    color: #0F172A;
    letter-spacing: -0.02em;
    line-height: 1;
  }

  .ov-day-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94A3B8;
  }

  .ov-day-date {
    font-size: 12px;
    font-weight: 500;
    color: #64748B;
    margin-left: auto;
  }

  /* ── EVENTS ── */
  .ov-transit-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #F1F5F9;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #475569;
    cursor: pointer;
    margin: 12px 0 12px 84px;
    font-weight: 500;
    transition: background 0.15s;
  }
  .ov-transit-btn:hover { background: #E2E8F0; color: #0F172A; }

  .ov-transit-steps {
    margin: 0 0 12px 84px;
    padding: 14px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .ov-step-row { display: flex; gap: 10px; align-items: flex-start; }
  .ov-step-bullet { width: 12px; flex-shrink: 0; padding-top: 4px; display: flex; justify-content: center; }
  .ov-step-dot { width: 4px; height: 4px; border-radius: 50%; background: #94A3B8; }
  
  .ov-step-badge {
    display: inline-flex;
    align-items: center;
    font-size: 9px;
    font-family: 'DM Mono', monospace;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    margin-right: 6px;
    letter-spacing: 0.02em;
  }
  .ov-step-text { font-size: 12px; color: #334155; line-height: 1.5; flex: 1; }
  .ov-step-dur { font-family: 'DM Mono', monospace; font-size: 10px; color: #94A3B8; flex-shrink: 0; }

  /* event card */
  .ov-event {
    display: flex;
    padding: 1rem 0;
    border-bottom: 1px solid #F1F5F9;
  }
  .ov-event:last-child { border-bottom: none; }
  .ov-event-inner { display: flex; width: 100%; align-items: start; }

  .ov-ev-time { width: 68px; flex-shrink: 0; padding-top: 4px; text-align: right; padding-right: 16px; }
  .ov-ev-time-start { font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 700; color: #0F172A; display: block; }
  .ov-ev-time-end { font-family: 'DM Mono', monospace; font-size: 10px; color: #94A3B8; display: block; margin-top: 1px; }

  .ov-ev-indicator { flex-shrink: 0; width: 16px; display: flex; flex-direction: column; align-items: center; padding-top: 8px; margin-right: 16px; }
  .ov-ev-dot { width: 8px; height: 8px; border-radius: 50%; background: #FFFFFF; border: 2px solid #CBD5E1; flex-shrink: 0; }
  .ov-ev-dot.filled { background: #3b82f6; border-color: #3b82f6; }
  .ov-ev-dot.meal { background: #F97316; border-color: #F97316; }
  .ov-ev-dot.logistics { background: #94A3B8; border-color: #94A3B8; }

  .ov-ev-body { flex: 1; min-width: 0; }
  .ov-ev-name-logistics { font-size: 13px; font-weight: 500; color: #64748B; }
  .ov-ev-name-meal { font-size: 13px; font-weight: 500; color: #F97316; }
  .ov-ev-name-main { font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 4px; letter-spacing: -0.01em; }

  .ov-ev-addr { font-size: 11px; color: #64748B; display: flex; align-items: center; gap: 4px; margin-bottom: 6px; }
  .ov-ev-desc { font-size: 12.5px; color: #475569; line-height: 1.6; margin: 8px 0; text-align: justify; padding-left: 12px; border-left: 2px solid #E2E8F0; }
  .ov-ev-link { font-family: 'DM Mono', monospace; font-size: 10px; color: #3b82f6; font-weight: 600; display: inline-flex; align-items: center; gap: 3px; margin-top: 4px; }
  .ov-ev-link:hover { text-decoration: underline; }

  .ov-ev-reservation {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    color: #B45309;
    background: #FEF3C7;
    border: 1px solid #FDE68A;
    padding: 2px 8px;
    border-radius: 4px;
    margin-top: 8px;
    letter-spacing: 0.02em;
  }

  .ov-ev-image {
    width: 80px;
    height: 80px;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    flex-shrink: 0;
    margin-left: 16px;
  }

  @media (max-width: 640px) {
    .ov-body { padding: 0 1.25rem 2rem; }
    .ov-masthead { padding: 1.75rem 1.5rem 1.5rem; }
    .ov-logistics-grid { grid-template-columns: 1fr; }
    .ov-ev-image { display: none; }
    .ov-transit-btn, .ov-transit-steps { margin-left: 32px; }
  }
`;

/* ─── HELPER PARSERS ─── */
const fmtDate = (d, opts = { day: 'numeric', month: 'short', year: 'numeric' }) => {
  if (!d) return '—';
  try { return new Date(d).toLocaleDateString('en-GB', opts); } catch { return d; }
};

const fmtDayLabel = d => fmtDate(d, { weekday: 'long', day: 'numeric', month: 'long' });

const fmtPrice = (price, ccy) =>
  price != null ? `${Number(price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${ccy || ''}` : null;

const isLogisticsEvent = ev => {
  const id = String(ev.id ?? '');
  return (
    id === 'arr_airport' || id === 'arr_hotel' || id === 'dep_airport' ||
    id.startsWith('start_hotel') || id.startsWith('return_hotel')
  );
};

const DAY_LABELS = ['Arrival Day', 'Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Departure Day'];


/* ─── NESTED ATTRACTION BLUEPRINT PARTS ─── */
function TransitSteps({ steps }) {
  return (
    <div className="ov-transit-steps">
      {steps.map((s, i) => (
        <div key={i} className="ov-step-row">
          <div className="ov-step-bullet"><div className="ov-step-dot" /></div>
          <div className="ov-step-text">
            {s.transit_detail && (
              <span className="ov-step-badge" style={{ background: s.transit_detail.bg_color || '#E2E8F0', color: s.transit_detail.text_color || '#0F172A' }}>
                {s.transit_detail.line_name}
              </span>
            )}
            {s.instruction}
          </div>
          <span className="ov-step-dur">{s.duration_mins}m</span>
        </div>
      ))}
    </div>
  );
}

function TransitAccordion({ path }) {
  const [open, setOpen] = useState(false);
  if (!path || !path.steps?.length) return null;
  return (
    <>
      <button className="ov-transit-btn" onClick={() => setOpen(v => !v)}>
        <span>{path.duration_mins}m transit · {path.distance_text || ''}</span>
        <ChevronDown size={11} style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }} />
      </button>
      {open && <TransitSteps steps={path.steps} />}
    </>
  );
}

function LogisticsGrid({ vacation, mobility }) {
  const flightPrice = fmtPrice(vacation.flight_price, vacation.flight_ccy);
  const hotelPrice = fmtPrice(vacation.accommodation_price, vacation.accommodation_ccy);
  const mobilityPrice = mobility?.price_est != null ? fmtPrice(mobility.price_est, mobility.currency || 'EUR') : null;

  return (
    <div className="ov-logistics-grid">
      <div className="ov-logistics-card">
        <div className="ov-lc-type">Flights</div>
        <div className="ov-lc-name">{vacation.airport_name || 'Self-arranged'}</div>
        {vacation.origin && <div className="ov-lc-sub">From {vacation.origin.replace(',', ' / ')}</div>}
        {vacation.flights_url && (
          <a className="ov-lc-link" href={vacation.flights_url} target="_blank" rel="noreferrer">
            Booking reference <ExternalLink size={9} />
          </a>
        )}
        {flightPrice && <div className="ov-lc-price">{flightPrice}</div>}
      </div>

      <div className="ov-logistics-card">
        <div className="ov-lc-type">Accommodation</div>
        <div className="ov-lc-name">{vacation.accommodation_name || 'Self-arranged'}</div>
        {vacation.accommodation_address && <div className="ov-lc-sub">{vacation.accommodation_address}</div>}
        {vacation.accommodation_url && (
          <a className="ov-lc-link" href={vacation.accommodation_url} target="_blank" rel="noreferrer">
            View booking <ExternalLink size={9} />
          </a>
        )}
        {hotelPrice && <div className="ov-lc-price">{hotelPrice}</div>}
      </div>

      <div className="ov-logistics-card">
        <div className="ov-lc-type">Ground transport</div>
        <div className="ov-lc-name">{mobility?.has_rental_car ? 'Rental car' : 'Public transit pass'}</div>
        {mobility?.operating_hours && (
          <div className="ov-lc-sub">Service {mobility.operating_hours.open}–{mobility.operating_hours.close}</div>
        )}
        {mobility?.official_link && (
          <a className="ov-lc-link" href={mobility.official_link} target="_blank" rel="noreferrer">
            Transit portal <ExternalLink size={9} />
          </a>
        )}
        {mobilityPrice && <div className="ov-lc-price">{mobilityPrice}</div>}
      </div>
    </div>
  );
}

function EventRow({ event }) {
  const logistics = isLogisticsEvent(event);
  const isMeal = event.type === 'meal';
  const isMain = !logistics && !isMeal;

  let dotClass = 'ov-ev-dot';
  if (isMain) dotClass += ' filled';
  else if (isMeal) dotClass += ' meal';
  else dotClass += ' logistics';

  return (
    <div className="ov-event">
      <div className="ov-event-inner">
        <div className="ov-ev-time">
          <span className="ov-ev-time-start">{event.start_time || ''}</span>
          {event.end_time && event.end_time !== event.start_time && (
            <span className="ov-ev-time-end">{event.end_time}</span>
          )}
        </div>

        <div className="ov-ev-indicator"><div className={dotClass} /></div>

        <div className="ov-ev-body">
          {logistics && <div className="ov-ev-name-logistics">{event.name}</div>}
          {isMeal && <div className="ov-ev-name-meal">{event.name}</div>}
          {isMain && (
            <>
              <div className="ov-ev-name-main">{event.name}</div>
              {event.formatted_address && (
                <div className="ov-ev-addr">
                  <MapPin size={10} style={{ flexShrink: 0 }} /> {event.formatted_address}
                </div>
              )}
              {event.description && <div className="ov-ev-desc">{event.description}</div>}
              {event.website_url && (
                <a className="ov-ev-link" href={event.website_url.split(';')[0]} target="_blank" rel="noreferrer">
                  Official website <ExternalLink size={9} />
                </a>
              )}
              {event.needs_reservation && (
                <div className="ov-ev-reservation"><AlertTriangle size={10} /> Advance booking required</div>
              )}
            </>
          )}
        </div>

        {isMain && event.image_url && (
          <img className="ov-ev-image" src={event.image_url} alt={event.name} loading="lazy" onError={e => { e.currentTarget.style.display = 'none'; }} />
        )}
      </div>
    </div>
  );
}

function DayBlock({ day }) {
  const label = DAY_LABELS[day.day_index] ?? `Day ${day.day_index + 1}`;
  return (
    <div className="ov-day">
      <div className="ov-day-header">
        <span className="ov-day-num">{label}</span>
        <span className="ov-day-label">—</span>
        <span className="ov-day-date">{fmtDayLabel(day.date)}</span>
      </div>
      <div className="ov-events">
        {(day.events || []).map((ev, eIdx) => (
          <React.Fragment key={ev.id ?? eIdx}>
            {ev.transit_path && <TransitAccordion path={ev.transit_path} />}
            {!ev.transit_path && (ev.transit_mins ?? 0) > 0 && (
              <button className="ov-transit-btn" style={{ cursor: 'default' }}>{ev.transit_mins}m transit</button>
            )}
            <EventRow event={ev} />
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}


/* ─── PRIMARY HISTORY ENTRY CANVAS ─── */
export default function History() {
  const [vacations, setVacations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedVacation, setSelectedVacation] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const calculateDays = (start, end) => {
    if (!start || !end) return "?";
    const diffTime = Math.abs(new Date(end) - new Date(start));
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
  };

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/history/vacations`, {}, "GET");
      if (res.ok) {
        setVacations(await res.json());
      }
    } catch (err) {
      console.error("Failed to load history:", err);
      toast.error("Failed to load your travel history.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDetails = async (tripId) => {
    const loadingToast = toast.loading("Unpacking structural blueprint...");
    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/history/vacations/${tripId}`, {}, "GET");
      if (res.ok) {
        setSelectedVacation(await res.json());
        toast.dismiss(loadingToast);
      } else {
        toast.error("Failed to read blueprint details logs.", { id: loadingToast });
      }
    } catch (err) {
      console.error(err);
      toast.error("Network connectivity failure.", { id: loadingToast });
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this trip blueprint permanently? This action is un-executable backward.")) return;

    try {
      const res = await fetchWithAuth(`${API_BASE_URL}/history/vacations/${id}`, {}, "DELETE");
      if (res.ok) {
        toast.success("Trip passport archived and wiped.");
        setVacations(prev => prev.filter(v => v.id !== id));
        if (selectedVacation?.id === id) setSelectedVacation(null);
      } else {
        toast.error("Authorization or execution server failure.");
      }
    } catch (err) {
      console.error(err);
      toast.error("An error occurred during deletion pass.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center h-screen bg-slate-50">
        <Loader2 className="animate-spin text-blue-600 mb-4" size={32} />
        <div className="text-slate-500 font-bold text-sm uppercase tracking-wider">Retrieving Secure Passports...</div>
      </div>
    );
  }

  // ─── RENDERS FULL ITINERARY BLUEPRINT VIEW (Overview Copy) ───
  if (selectedVacation) {
    const mobility = selectedVacation.itinerary_data?.mobility;
    const timeline = selectedVacation.itinerary_data?.timeline ?? [];

    return (
      <PageTransition className="min-h-screen bg-slate-50 p-4 md:p-8 overflow-y-auto w-full">
        <Toaster position="top-center" />
        <style>{css}</style>
        
        <div className="max-w-4xl mx-auto space-y-4">
          <button 
            onClick={() => setSelectedVacation(null)}
            className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-400 hover:text-slate-900 transition-colors mb-2"
          >
            <ArrowLeft size={14} /> Back to Passport List
          </button>

          <div className="ov-sheet animate-fadeIn">
            {/* ── MASTHEAD ── */}
            <div className="ov-masthead">
              <div className="ov-eyebrow">Archived travel log · {fmtShort(selectedVacation.created_at)}</div>
              <h1 className="ov-destination">{selectedVacation.destination}</h1>
              <div className="ov-dates">{fmtShort(selectedVacation.from_date)} — {fmtShort(selectedVacation.to_date)}</div>

              <div className="ov-masthead-meta">
                <div className="ov-meta-item">
                  <span className="ov-meta-label">Travellers</span>
                  <span className="ov-meta-value">
                    {selectedVacation.adults} adult{selectedVacation.adults !== 1 ? 's' : ''}
                    {selectedVacation.children > 0 ? ` · ${selectedVacation.children} child${selectedVacation.children !== 1 ? 'ren' : ''}` : ''}
                  </span>
                </div>
                {selectedVacation.origin && (
                  <div className="ov-meta-item">
                    <span className="ov-meta-label">Departing from</span>
                    <span className="ov-meta-value">{selectedVacation.origin.replace(',', ' / ')}</span>
                  </div>
                )}
                <div className="ov-meta-item">
                  <span className="ov-meta-label">Reference ID</span>
                  <span className="ov-meta-value" style={{ fontFamily: 'DM Mono, monospace', fontSize: 11, opacity: 0.55 }}>
                    {selectedVacation.id}
                  </span>
                </div>
              </div>
            </div>

            {/* ── BODY ── */}
            <div className="ov-body">
              {/* Logistics */}
              <div className="ov-section">
                <div className="ov-section-rule">
                  <span className="ov-section-num">I.</span>
                  <span className="ov-section-title">Arranged logistics</span>
                  <div className="ov-rule" />
                </div>
                <LogisticsGrid vacation={selectedVacation} mobility={mobility} />
              </div>

              {/* Itinerary */}
              <div className="ov-section">
                <div className="ov-section-rule">
                  <span className="ov-section-num">II.</span>
                  <span className="ov-section-title">Daily itinerary</span>
                  <div className="ov-rule" />
                </div>
                {timeline.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 text-xs border border-dashed rounded-xl">
                    No timeline checkpoints stored for this entry.
                  </div>
                ) : (
                  timeline.map((day, dIdx) => <DayBlock key={day.day_index} day={day} />)
                )}
              </div>
            </div>

          </div>
        </div>
      </PageTransition>
    );
  }

  // ─── RENDERS PASSPORT SELECTION INDEX GRID LIST ───
  return (
    <PageTransition className="min-h-screen bg-slate-50 p-6 md:p-12 font-sans w-full">
      <Toaster position="top-center" />
      <div className="max-w-6xl mx-auto space-y-8">
        
        <header className="border-b border-slate-200 pb-6">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-blue-600 bg-blue-50 px-3 py-1 rounded-full border border-blue-100 w-fit mb-3">
            <Compass size={12} /> Vault Registry
          </div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">Travel Passports</h1>
          <p className="text-sm font-semibold text-slate-400 mt-1">An archival ledger containing your immutable finalized trip blueprints.</p>
        </header>

        {vacations.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-slate-200 shadow-sm">
            <MapPin className="mx-auto text-slate-300 mb-4 animate-bounce" size={44} />
            <h3 className="text-lg font-black text-slate-700">No historical records located</h3>
            <p className="text-xs text-slate-400 mt-1 font-medium">Complete an active itinerary timeline sequence inside the wizard block to index entries.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fadeIn">
            {vacations.map((trip) => {
              const daysCount = calculateDays(trip.from_date, trip.to_date);
               
              return (
                <div 
                  key={trip.id} 
                  onClick={() => handleViewDetails(trip.id)}
                  className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer group overflow-hidden flex flex-col relative"
                >
                  {/* Delete Trigger Overlay Button */}
                  <button 
                    onClick={(e) => handleDelete(trip.id, e)}
                    className="absolute top-4 right-4 z-20 p-2 bg-slate-900/40 hover:bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all backdrop-blur-md shadow-md"
                    title="Purge Document Matrix Permanently"
                  >
                    <Trash2 size={14} />
                  </button>

                  {/* Card Title Box */}
                  <div className="bg-slate-900 p-6 text-white relative overflow-hidden transition-colors group-hover:bg-slate-950">
                    <div className="relative z-10 pr-6">
                      <h2 className="text-xl font-black mb-1 tracking-tight truncate">{trip.destination}</h2>
                      <p className="text-slate-400 text-xs font-mono flex items-center gap-1.5 uppercase tracking-wider">
                        <MapPin size={12} className="text-sky-400" /> From {trip.origin || "Home Anchor"}
                      </p>
                    </div>
                    <div className="absolute -right-6 -top-6 w-20 h-20 bg-white/5 rounded-full blur-lg group-hover:scale-150 transition-transform duration-500"></div>
                  </div>

                  {/* Body Content Blocks */}
                  <div className="p-5 flex-1 flex flex-col gap-4">
                    <div className="flex items-center justify-center gap-2 text-xs font-mono font-bold text-slate-600 bg-slate-50 py-2.5 rounded-xl border border-slate-100">
                      <Calendar size={14} className="text-blue-500" />
                      {fmtShort(trip.from_date)} <ArrowRight size={10} className="text-slate-300" /> {fmtShort(trip.to_date)}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className={`flex flex-col items-center justify-center gap-1 p-2.5 rounded-xl border ${trip.flight_price ? 'border-blue-100 bg-blue-50/50 text-blue-700' : 'border-slate-100 bg-slate-50 text-slate-400 opacity-60'} text-[10px] font-black uppercase tracking-wider`}>
                        <Plane size={16} /> 
                        <span className="truncate max-w-full font-mono mt-0.5">{trip.flight_price ? `${trip.flight_price.toLocaleString()} ${trip.flight_ccy}` : 'No Flight Data'}</span>
                      </div>
                      <div className={`flex flex-col items-center justify-center gap-1 p-2.5 rounded-xl border ${trip.accommodation_price ? 'border-emerald-100 bg-emerald-50/50 text-emerald-700' : 'border-slate-100 bg-slate-50 text-slate-400 opacity-60'} text-[10px] font-black uppercase tracking-wider`}>
                        <Building size={16} />
                        <span className="truncate max-w-full font-mono mt-0.5">{trip.accommodation_price ? `${trip.accommodation_price.toLocaleString()} ${trip.accommodation_ccy}` : 'No Hotel Data'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Footer Stats Metadata Row */}
                  <div className="px-5 py-4 border-t border-slate-100 bg-slate-50/50 flex justify-between items-center group-hover:bg-blue-50/40 transition-colors">
                    <div className="flex flex-col">
                      <span className="text-[9px] font-black text-slate-400 group-hover:text-blue-500 uppercase tracking-widest transition-colors">
                        {daysCount} Days Scheduled
                      </span>
                      {trip.created_at && (
                        <span className="text-[9px] font-bold text-slate-400 mt-0.5">
                          Archived {fmtShort(trip.created_at)}
                        </span>
                      )}
                    </div>
                    
                    <span className="text-blue-600 font-bold text-xs flex items-center gap-0.5 group-hover:text-blue-800 transition-colors">
                      Unpack Blueprint <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
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
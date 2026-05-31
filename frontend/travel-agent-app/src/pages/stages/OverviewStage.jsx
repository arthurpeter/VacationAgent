import React, { useEffect, useState } from 'react';
import { useOutletContext, useParams, useLocation, useNavigate } from 'react-router-dom';
import {
  Loader2,
  AlertTriangle,
  CheckCircle,
  ArrowRight,
  ChevronDown,
  ExternalLink,
  MapPin,
} from 'lucide-react';
import { fetchWithAuth } from '../../authService';
import { API_BASE_URL } from '../../config';
// 🟢 Optional: If using react-hot-toast or react-toastify, import it here. 
// Otherwise, a clean embedded custom toast alert state fallback is wired below.
import { toast } from 'react-hot-toast'; 

/* ─────────────────────────────────────────
   INLINE STYLES — PDF-grade editorial look
   Playfair Display (serif) + DM Mono (mono)
   Cream paper, precise typography, zero fluff
───────────────────────────────────────── */
const FONT_URL =
  'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,700;1,400;1,500&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap';

const css = `
  @import url('${FONT_URL}');

  .ov-root * { box-sizing: border-box; }

  .ov-root {
    font-family: 'DM Sans', sans-serif;
    background: #F9F6F1;
    width: 100%;
    height: calc(100vh - 73px);
    overflow-y: scroll !important;
    display: block;
    padding: 2.5rem 1.5rem 5rem;
    color: #1a1714;
  }

  .ov-sheet {
    max-width: 820px;
    margin: 0 auto;
    background: #FDFBF8;
    border: 0.5px solid #DDD9D2;
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 4px 32px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04);
  }

  /* ── MASTHEAD ── */
  .ov-masthead {
    background: #0F172A; /* Deep premium slate-dark background */
    color: #FFFFFF;
    padding: 3rem 3rem 2.5rem;
    position: relative;
    overflow: hidden;
    border-bottom: 1px solid #1E293B;
  }

  .ov-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #38BDF8; /* Clean electric blue token highlight */
    margin-bottom: 0.6rem;
    font-weight: 500;
  }

  .ov-destination {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 900; /* Ultra thick modern weight instead of serif */
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin: 0 0 0.5rem;
    color: #FFFFFF;
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

  .ov-meta-value {
    font-size: 13px;
    font-weight: 500;
    color: #E2E8F0;
  }

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

  .ov-rule {
    flex: 1;
    height: 1px;
    background: #F1F5F9;
  }

  /* ── LOGISTICS STRIP ── */
  .ov-logistics-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px; /* Ditch the 1px divider for a clean gap layout grid */
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
    color: #0EA5E9; /* Premium structural blue text */
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
  .ov-day {
    margin-bottom: 3rem;
  }

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
  .ov-ev-desc { font-size: 12.5px; color: #475569; line-height: 1.6; margin: 8px 0; text-align: justify; padding-left: 12px; border-left: 1px solid #DDD9D2; }
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

  /* ── FINALIZE BAR ── */
  .ov-finalize {
    margin: 3rem;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    flex-wrap: wrap;
    background: #F8FAFC;
  }

  .ov-finalize-text h4 { font-size: 16px; font-weight: 700; margin: 0 0 4px; color: #0F172A; }
  .ov-finalize-text p { font-size: 12px; color: #64748B; margin: 0; max-w: 380px; line-height: 1.5; }

  .ov-finalize-btn {
    background: #0F172A;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: background 0.15s;
  }
  .ov-finalize-btn:hover { background: #1E293B; }
  .ov-finalize-btn:disabled { opacity: 0.4; cursor: default; }
`;

/* ─── helpers ─────────────────────────────── */
const fmtDate = (d, opts = { day: 'numeric', month: 'long', year: 'numeric' }) => {
  if (!d) return '—';
  try { return new Date(d).toLocaleDateString('en-GB', opts); } catch { return d; }
};

const fmtShort = d => fmtDate(d, { day: 'numeric', month: 'short', year: 'numeric' });
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

/* ─── DAY NAMES ─────────────────────────── */
const DAY_LABELS = ['Arrival Day', 'Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Departure Day'];

/* ─── SUB-COMPONENTS ─────────────────────── */
function TransitSteps({ steps }) {
  return (
    <div className="ov-transit-steps">
      {steps.map((s, i) => (
        <div key={i} className="ov-step-row">
          <div className="ov-step-bullet">
            <div className="ov-step-dot" />
          </div>
          <div className="ov-step-text">
            {s.transit_detail && (
              <span
                className="ov-step-badge"
                style={{
                  background: s.transit_detail.bg_color || '#DDD9D2',
                  color: s.transit_detail.text_color || '#1a1714',
                }}
              >
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
        <ChevronDown
          size={11}
          style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}
        />
      </button>
      {open && <TransitSteps steps={path.steps} />}
    </>
  );
}

function LogisticsGrid({ vacation, mobility }) {
  const flightPrice = fmtPrice(vacation.flight_price, vacation.flight_ccy);
  const hotelPrice = fmtPrice(vacation.accommodation_price, vacation.accommodation_ccy);
  const mobilityPrice = mobility?.price_est != null
    ? fmtPrice(mobility.price_est, mobility.currency || 'EUR')
    : null;

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
        {vacation.accommodation_address && (
          <div className="ov-lc-sub">{vacation.accommodation_address}</div>
        )}
        {vacation.accommodation_url && (
          <a className="ov-lc-link" href={vacation.accommodation_url} target="_blank" rel="noreferrer">
            View booking <ExternalLink size={9} />
          </a>
        )}
        {hotelPrice && <div className="ov-lc-price">{hotelPrice}</div>}
      </div>

      <div className="ov-logistics-card">
        <div className="ov-lc-type">Ground transport</div>
        <div className="ov-lc-name">
          {mobility?.has_rental_car ? 'Rental car' : 'Public transit pass'}
        </div>
        {mobility?.operating_hours && (
          <div className="ov-lc-sub">
            Service {mobility.operating_hours.open}–{mobility.operating_hours.close}
          </div>
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

  const url = event.website_url ? event.website_url.split(';')[0] : null;

  return (
    <div className="ov-event">
      <div className="ov-event-inner">
        <div className="ov-ev-time">
          <span className="ov-ev-time-start">{event.start_time || ''}</span>
          {event.end_time && event.end_time !== event.start_time && (
            <span className="ov-ev-time-end">{event.end_time}</span>
          )}
        </div>

        <div className="ov-ev-indicator">
          <div className={dotClass} />
        </div>

        <div className="ov-ev-body">
          {logistics && <div className="ov-ev-name-logistics">{event.name}</div>}
          {isMeal && <div className="ov-ev-name-meal">{event.name}</div>}
          {isMain && (
            <>
              <div className="ov-ev-name-main">{event.name}</div>
              {event.formatted_address && (
                <div className="ov-ev-addr">
                  <MapPin size={10} style={{ flexShrink: 0 }} />
                  {event.formatted_address}
                </div>
              )}
              {event.description && (
                <div className="ov-ev-desc">{event.description}</div>
              )}
              {url && (
                <a className="ov-ev-link" href={url} target="_blank" rel="noreferrer">
                  Official website <ExternalLink size={9} />
                </a>
              )}
              {event.needs_reservation && (
                <div className="ov-ev-reservation">
                  <AlertTriangle size={10} /> Advance booking required
                </div>
              )}
            </>
          )}
        </div>

        {isMain && event.image_url && (
          <img
            className="ov-ev-image"
            src={event.image_url}
            alt={event.name}
            loading="lazy"
            onError={e => { e.currentTarget.style.display = 'none'; }}
          />
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
              <button className="ov-transit-btn" style={{ cursor: 'default' }}>
                {ev.transit_mins}m transit
              </button>
            )}
            <EventRow event={ev} />
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

/* ─── MAIN COMPONENT ─────────────────────── */
export default function OverviewStage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate(); // 🟢 Used for routing back home upon successful finalization pass
  
  const context = useOutletContext();
  const handleLayoutFinalize = context?.handleFinalizeTrip;

  const [vacationDetails, setVacationDetails] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFinalizing, setIsFinalizing] = useState(false); // 🟢 Local submission tracker variable

  const isHistoryView = location.pathname.includes('/history') || !handleLayoutFinalize;

  useEffect(() => {
    const initializeOverviewData = async () => {
      try {
        setIsLoading(true);
        if (!isHistoryView) {
          const compileRes = await fetchWithAuth(`${API_BASE_URL}/session/compile/${id}`, {}, "POST");
          if (compileRes && compileRes.ok) {
            const compileData = await compileRes.json();
            const detailRes = await fetchWithAuth(`${API_BASE_URL}/history/vacations/${compileData.vacation_id}`, {}, "GET");
            if (detailRes && detailRes.ok) {
              setVacationDetails(await detailRes.json());
            }
          }
        } else {
          const detailRes = await fetchWithAuth(`${API_BASE_URL}/history/vacations/${id}`, {}, "GET");
          if (detailRes && detailRes.ok) {
            setVacationDetails(await detailRes.json());
          }
        }
      } catch (error) {
        console.error("Monolithic overview state resolution failure:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      initializeOverviewData();
    }
  }, [id, isHistoryView]);

  // ─── CLICK INTERCEPTOR ───
  const handleFinalizeTripClick = async () => {
    try {
      setIsFinalizing(true);
      // 1. Fire execution signal to your backend session router path
      const res = await fetchWithAuth(`${API_BASE_URL}/session/finalize/${id}`, {}, "POST");
      
      if (res && res.ok) {
        // 2. Dispatch alert validation notice (supports hot-toast and window native configurations)
        const successMessage = "Your itinerary PDF is compiling and will arrive in your email shortly.";
        if (typeof toast !== 'undefined' && toast.success) {
          toast.success(successMessage);
        } else {
          alert(successMessage);
        }
        
        // 3. Kick user out of the active editing workflow context back to the primary landing frame
        navigate('/');
      } else {
        if (typeof toast !== 'undefined' && toast.error) {
          toast.error("Turbulence encountered: Failed to serialize and seal vacation record.");
        }
      }
    } catch (err) {
      console.error("Finalization pass network intercept error:", err);
      if (typeof toast !== 'undefined' && toast.error) {
        toast.error("Connection failure: Could not link to documentation dispatch sockets.");
      }
    } finally {
      setIsFinalizing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-grow flex flex-col items-center justify-center bg-gray-50 h-full w-full">
        <Loader2 className="animate-spin text-blue-600 mb-4" size={40} />
        <h3 className="font-black text-lg text-slate-900">
          {isHistoryView ? 'Retrieving Archived Trip Blueprint' : 'Assembling Itinerary Blueprint'}
        </h3>
        <p className="text-xs text-slate-400 mt-1">Normalizing routing vectors, steps, and reservation metadata...</p>
      </div>
    );
  }

  if (!vacationDetails) {
    return (
      <div className="flex-grow flex flex-col items-center justify-center text-slate-400 p-8 text-sm w-full h-full">
        <AlertTriangle size={32} className="text-amber-500 mb-2" />
        No explicit matching itinerary matrix could be parsed for this record.
      </div>
    );
  }

  const mobility = vacationDetails.itinerary_data?.mobility;
  const timeline = vacationDetails.itinerary_data?.timeline ?? [];

  return (
    <>
      <style>{css}</style>

      <div className="ov-root">
        <div className="ov-sheet">

          {/* ── MASTHEAD ── */}
          <div className="ov-masthead">
            <div className="ov-eyebrow">
              {isHistoryView ? 'Archived itinerary' : 'Travel manifest'} · {fmtShort(vacationDetails.created_at)}
            </div>

            <h1 className="ov-destination">{vacationDetails.destination}</h1>

            <div className="ov-dates">
              {fmtShort(vacationDetails.from_date)} — {fmtShort(vacationDetails.to_date)}
            </div>

            <div className="ov-masthead-meta">
              <div className="ov-meta-item">
                <span className="ov-meta-label">Travellers</span>
                <span className="ov-meta-value">
                  {vacationDetails.adults} adult{vacationDetails.adults !== 1 ? 's' : ''}
                  {vacationDetails.children > 0 ? ` · ${vacationDetails.children} child${vacationDetails.children !== 1 ? 'ren' : ''}` : ''}
                </span>
              </div>
              {vacationDetails.origin && (
                <div className="ov-meta-item">
                  <span className="ov-meta-label">Departing from</span>
                  <span className="ov-meta-value">{vacationDetails.origin.replace(',', ' / ')}</span>
                </div>
              )}
              <div className="ov-meta-item">
                <span className="ov-meta-label">Reference ID</span>
                <span className="ov-meta-value" style={{ fontFamily: 'DM Mono, monospace', fontSize: 11, opacity: 0.55 }}>
                  {(vacationDetails.id || id || '—').slice(0, 18)}…
                </span>
              </div>
            </div>
          </div>

          {/* ── BODY ── */}
          <div className="ov-body">

            {/* SECTION 1 — Logistics */}
            <div className="ov-section">
              <div className="ov-section-rule">
                <span className="ov-section-num">I.</span>
                <span className="ov-section-title">Arranged logistics</span>
                <div className="ov-rule" />
              </div>
              <LogisticsGrid vacation={vacationDetails} mobility={mobility} />
            </div>

            {/* SECTION 2 — Itinerary */}
            <div className="ov-section">
              <div className="ov-section-rule">
                <span className="ov-section-num">II.</span>
                <span className="ov-section-title">Daily itinerary</span>
                <div className="ov-rule" />
              </div>

              {timeline.map((day, dIdx) => (
                <DayBlock key={day.day_index} day={day} dIdx={dIdx} />
              ))}
            </div>

          </div>

          {/* ── FINALIZE BAR ── */}
          {!isHistoryView && (
            <div className="ov-finalize">
              <div className="ov-finalize-text">
                <h4>Ready to confirm this itinerary?</h4>
                <p>
                  Locking the manifest will dispatch a formatted PDF copy to your registered email.
                </p>
              </div>
              <button
                className="ov-finalize-btn"
                onClick={handleFinalizeTripClick}
                disabled={!!isFinalizing}
              >
                {isFinalizing ? (
                  <>
                    <Loader2 size={13} className="animate-spin" /> Generating…
                  </>
                ) : (
                  <>
                    Confirm & dispatch <ArrowRight size={13} />
                  </>
                )}
              </button>
            </div>
          )}

        </div>
      </div>
    </>
  );
}
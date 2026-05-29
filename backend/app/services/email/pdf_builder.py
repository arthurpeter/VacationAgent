import asyncio
import os
import json
from datetime import datetime
import sys
from typing import Dict, Any
import weasyprint

from app.core.logger import get_logger

logger = get_logger(__name__)

def format_short_date(date_str: str) -> str:
    if not date_str:
        return "—"
    try:
        # Handles both ISO strings and plain date formats
        clean_date = date_str.split("T")[0]
        dt = datetime.strptime(clean_date, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str

def format_day_label(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        clean_date = date_str.split("T")[0]
        dt = datetime.strptime(clean_date, "%Y-%m-%d")
        return dt.strftime("%A, %B %d")
    except Exception:
        return ""

def generate_itinerary_pdf(vacation_data: Dict[str, Any]) -> bytes:
    """
    Compiles a compiled Vacation dictionary payload into an unmodifiable,
    high-contrast modern PDF binary byte stream ready for email dispatch.
    """
    itinerary_data = vacation_data.get("itinerary_data", {}) or {}
    mobility = itinerary_data.get("mobility", {})
    timeline = itinerary_data.get("timeline", [])
    
    # 1. Base Currency Snapshot Resolutions
    ccy = itinerary_data.get("meta", {}).get("currency", "EUR")
    flight_price = f"{vacation_data.get('flight_price'):,.2f} {vacation_data.get('flight_ccy') or ccy}" if vacation_data.get('flight_price') else "—"
    hotel_price = f"{vacation_data.get('accommodation_price'):,.2f} {vacation_data.get('accommodation_ccy') or ccy}" if vacation_data.get('accommodation_price') else "—"
    mobility_price = f"{mobility.get('price_est'):,.2f} {mobility.get('currency') or ccy}" if mobility.get('price_est') else "0.00 EUR"

    # 2. Build the Document Top Metadata Headers
    passenger_capacity = f"{vacation_data.get('adults', 1)} Adult(s)"
    if vacation_data.get("children", 0) > 0:
        passenger_capacity += f" · {vacation_data.get('children')} Child(ren)"

    # 3. Dynamic Chronological Step Iterator Loop Assembly
    timeline_html_blocks = []
    day_labels = ['Arrival Day', 'Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Departure Day']
    
    for idx, day in enumerate(timeline):
        day_index = day.get("day_index", idx)
        label = day_labels[day_index] if day_index < len(day_labels) else f"Day {day_index + 1}"
        
        day_header = f"""
        <div class="ov-day-header">
            <span class="ov-day-num">{label}</span>
            <span class="ov-day-label">—</span>
            <span class="ov-day-date">{format_day_label(day.get('date'))}</span>
        </div>
        """
        
        event_rows = []
        for event in day.get("events", []):
            event_id = str(event.get("id") or '')
            is_logistics = event_id in ['arr_airport', 'arr_hotel', 'dep_airport'] or event_id.startswith(('start_hotel', 'return_hotel'))
            is_meal = event.get("type") == 'meal'
            
            # Resolve Event Visual Archetype Tokens
            if is_logistics:
                card_class = "ov-event card-logistics"
                dot_class = "ov-ev-dot dot-logistics"
            elif is_meal:
                card_class = "ov-event card-meal"
                dot_class = "ov-ev-dot dot-meal"
            else:
                card_class = "ov-event card-main"
                dot_class = "ov-ev-dot dot-filled"

            # Dynamic Subtitle Content Assembly
            content_body = f'<div class="ov-ev-title-text">{event.get("name")}</div>'
            if not is_logistics and not is_meal:
                if event.get("formatted_address"):
                    content_body += f'<div class="ov-ev-addr">📍 {event.get("formatted_address")}</div>'
                if event.get("description"):
                    content_body += f'<div class="ov-ev-desc">{event.get("description")}</div>'
                if event.get("needs_reservation"):
                    content_body += '<div class="ov-ev-reservation">⚠️ Advance Booking Required</div>'

            # Flatten and Append Transit Connection Steps Natively
            transit_html = ""
            transit_path = event.get("transit_path")
            if transit_path and transit_path.get("steps"):
                step_items = []
                for step in transit_path["steps"]:
                    badge = ""
                    if step.get("transit_detail"):
                        bg = step["transit_detail"].get("bg_color", "#E2E8F0")
                        txt = step["transit_detail"].get("text_color", "#0F172A")
                        badge = f'<span class="ov-step-badge" style="background: {bg}; color: {txt};">{step["transit_detail"].get("line_name")}</span>'
                    
                    step_items.append(f"""
                        <div class="ov-step-row">
                            <span class="ov-step-text">{badge}{step.get('instruction')}</span>
                            <span class="ov-step-dur">{step.get('duration_mins')}m</span>
                        </div>
                    """)
                
                transit_html = f"""
                <div class="ov-transit-container">
                    <div class="ov-transit-title">⚡ {transit_path.get('duration_mins')}m Transit Link · ({transit_path.get('distance_text', 'Est')})</div>
                    <div class="ov-transit-steps">{"".join(step_items)}</div>
                </div>
                """
            elif event.get("transit_mins", 0) > 0:
                transit_html = f"""
                <div class="ov-transit-container">
                    <div class="ov-transit-title">⚡ {event.get('transit_mins')}m Local Area Transit</div>
                </div>
                """

            event_rows.append(f"""
            {transit_html}
            <div class="{card_class}">
                <div class="ov-ev-time">
                    <span class="ov-ev-time-start">{event.get('start_time', '')}</span>
                    <span class="ov-ev-time-end">{event.get('end_time', '')}</span>
                </div>
                <div class="ov-ev-indicator">
                    <div class="{dot_class}"></div>
                </div>
                <div class="ov-ev-body">
                    {content_body}
                </div>
            </div>
            """)

        timeline_html_blocks.append(f"""
        <div class="ov-day">
            {day_header}
            <div class="ov-events">
                {"".join(event_rows)}
            </div>
        </div>
        """)

    # 4. Inject Dynamic Blocks into the Blueprint Master Template Frame
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4;
            margin: 20mm 15mm;
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 8pt;
                color: #94A3B8;
            }}
            @bottom-left {{
                content: "TuRAG AI Engine Master Travel Blueprint Manifest";
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 8pt;
                font-weight: bold;
                color: #94A3B8;
            }}
        }}
        
        body {{
            font-family: Arial, sans-serif;
            color: #0F172A;
            line-height: 1.5;
            font-size: 10pt;
            background-color: #FFFFFF;
            margin: 0; padding: 0;
        }}

        /* ── HEADER PRESENTATION LAYER ── */
        .ov-masthead {{
            background: #0F172A;
            color: #FFFFFF;
            padding: 24pt 24pt 20pt;
            border-radius: 8px;
            margin-bottom: 20pt;
        }}
        .ov-eyebrow {{
            font-size: 8pt;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: #38BDF8;
            margin-bottom: 4pt;
            font-weight: bold;
        }}
        .ov-destination {{
            font-size: 24pt;
            font-weight: 900;
            margin: 0 0 4pt 0;
            letter-spacing: -0.5px;
        }}
        .ov-dates {{
            font-size: 10pt;
            color: #94A3B8;
            margin-bottom: 12pt;
        }}
        .ov-meta-table {{
            width: 100%;
            border-top: 1px solid #1E293B;
            padding-top: 10pt;
            margin-top: 10pt;
        }}
        .ov-meta-label {{
            font-size: 7.5pt;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #64748B;
        }}
        .ov-meta-value {{
            font-size: 9.5pt;
            color: #E2E8F0;
            font-weight: bold;
        }}

        /* ── LOGISTICS LEDGER TABLE ── */
        .ov-section-title {{
            font-size: 8.5pt;
            font-weight: bold;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #64748B;
            margin: 20pt 0 8pt;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 3pt;
            page-break-after: avoid;
        }}
        .ledger-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20pt;
        }}
        .ledger-table th {{
            background-color: #F8FAFC;
            border-bottom: 2px solid #E2E8F0;
            color: #64748B;
            font-size: 8pt;
            font-weight: bold;
            text-transform: uppercase;
            padding: 6pt 8pt;
        }}
        .ledger-table td {{
            padding: 8pt;
            border-bottom: 1px solid #F1F5F9;
            font-size: 9pt;
        }}
        .price-col {{
            font-weight: bold;
            color: #0F172A;
            text-align: right;
        }}

        /* ── CHRONOLOGY TRACK LINES ── */
        .ov-day {{
            margin-bottom: 20pt;
            page-break-inside: auto;
        }}
        .ov-day-header {{
            background: #F8FAFC;
            border-bottom: 1px solid #E2E8F0;
            padding: 6pt 8pt;
            margin-bottom: 10pt;
            page-break-inside: avoid;
            page-break-after: avoid;
        }}
        .ov-day-num {{
            font-size: 14pt;
            font-weight: 900;
            color: #0F172A;
        }}
        .ov-day-date {{
            float: right;
            font-size: 9.5pt;
            color: #64748B;
            font-weight: bold;
            margin-top: 3pt;
        }}
        .ov-event {{
            display: table;
            width: 100%;
            margin-bottom: 8pt;
            border: 1px solid #F1F5F9;
            border-radius: 6px;
            padding: 8pt;
            page-break-inside: avoid;
        }}
        .card-logistics {{ background-color: #F8FAFC; border-style: dashed; border-color: #CBD5E1; }}
        .card-meal {{ background-color: #FFFDF9; border-color: #FED7AA; }}
        .card-main {{ background-color: #FFFFFF; border-color: #E2E8F0; }}
        
        .ov-ev-time {{ display: table-cell; width: 55pt; vertical-align: top; }}
        .ov-ev-time-start {{ font-size: 10pt; font-weight: bold; color: #0F172A; display: block; }}
        .ov-ev-time-end {{ font-size: 8pt; color: #94A3B8; display: block; }}
        
        .ov-ev-indicator {{ display: table-cell; width: 20pt; vertical-align: top; text-align: center; }}
        .ov-ev-dot {{ width: 6pt; height: 6pt; border-radius: 50%; display: inline-block; margin-top: 3pt; }}
        .dot-filled {{ background: #3B82F6; }}
        .dot-meal {{ background: #F97316; }}
        .dot-logistics {{ background: #94A3B8; }}
        
        .ov-ev-body {{ display: table-cell; vertical-align: top; padding-left: 4pt; }}
        .ov-ev-title-text {{ font-size: 11pt; font-weight: bold; color: #0F172A; }}
        .ov-ev-addr {{ font-size: 8.5pt; color: #64748B; margin-top: 2pt; }}
        .ov-ev-desc {{ font-size: 9pt; color: #475569; margin: 5pt 0; text-align: justify; padding-left: 8pt; border-left: 2px solid #E2E8F0; }}
        .ov-ev-reservation {{ display: inline-block; font-size: 7.5pt; font-weight: bold; background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; padding: 1pt 5pt; border-radius: 4px; margin-top: 4pt; text-transform: uppercase; }}

        /* ── FLATTENED STATIC TRANSIT Link LINES ── */
        .ov-transit-container {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-left: 3px solid #3B82F6;
            border-radius: 6px;
            padding: 6pt 10pt;
            margin: 4pt 0 4pt 55pt;
            page-break-inside: avoid;
        }}
        .ov-transit-title {{ font-size: 8.5pt; font-weight: bold; color: #334155; }}
        .ov-transit-steps {{ margin-top: 4pt; border-top: 1px solid #E2E8F0; padding-top: 4pt; }}
        .ov-step-row {{ display: table; width: 100%; margin-bottom: 2pt; font-size: 8pt; color: #475569; }}
        .ov-step-text {{ display: table-cell; vertical-align: top; }}
        .ov-step-dur {{ display: table-cell; width: 30pt; text-align: right; color: #94A3B8; font-weight: bold; }}
        .ov-step-badge {{ display: inline-block; font-size: 7.5pt; font-weight: bold; padding: 0.5pt 4pt; border-radius: 3px; margin-right: 4pt; }}
    </style>
    </head>
    <body>

        <div class="ov-masthead">
            <div class="ov-eyebrow">Master Blueprinted Itinerary Document</div>
            <div class="ov-destination">{vacation_data.get('destination', 'Your Itinerary')}</div>
            <div class="ov-dates">{format_short_date(vacation_data.get('from_date'))} — {format_short_date(vacation_data.get('to_date'))}</div>
            
            <table class="ov-meta-table">
                <tr>
                    <td>
                        <div class="ov-meta-label">Group Manifest</div>
                        <div class="ov-meta-value">{passenger_capacity}</div>
                    </td>
                    <td>
                        <div class="ov-meta-label">Departing From</div>
                        <div class="ov-meta-value">{vacation_data.get('origin', '—').replace(',', ' / ')}</div>
                    </td>
                    <td style="text-align: right;">
                        <div class="ov-meta-label">System Passport Tracking Reference</div>
                        <div class="ov-meta-value">ID: #{vacation_data.get('id', '—')}</div>
                    </td>
                </tr>
            </table>
        </div>

        <div class="ov-section-title">1. Arranged Logistics Ledger Summary</div>
        <table class="ledger-table">
            <thead>
                <tr>
                    <th style="width: 25%; text-align: left;">Segment Channel</th>
                    <th style="width: 55%; text-align: left;">Arranged Vendor Asset / Description</th>
                    <th style="width: 20%; text-align: right;">Accounting Balance</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight: bold;">✈️ Transit</td>
                    <td>{vacation_data.get('airport_name') or 'Self-Arranged Base Route'}</td>
                    <td class="price-col">{flight_price}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">🏨 Lodging</td>
                    <td>
                        <div style="font-weight: bold;">{vacation_data.get('accommodation_name') or 'Self-Arranged Base Stay'}</div>
                        <div style="font-size: 8pt; color: #64748B; margin-top: 1pt;">{vacation_data.get('accommodation_address') or ''}</div>
                    </td>
                    <td class="price-col">{hotel_price}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">{ '🚖' if mobility.get('has_rental_car') else '🚇' } Ground Network</td>
                    <td>{ 'Private Vehicle Lease' if mobility.get('has_rental_car') else 'Public Network Route Pass' }</td>
                    <td class="price-col">{mobility_price}</td>
                </tr>
            </tbody>
        </table>

        <div class="ov-section-title">2. Operational Chronology Blueprint</div>
        {"".join(timeline_html_blocks)}

    </body>
    </html>
    """

    # 5. Generate and return the static raw PDF bytes using WeasyPrint
    return weasyprint.HTML(string=html_content).write_pdf()


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app import models

async def _run_local_test(target_session_id: int):
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    print(f"📡 Booting connection to database engine...")
    engine = create_async_engine(db_url, echo=False)
    
    async with AsyncSession(engine) as session:
        print(f"🔍 Querying record for session_id: {target_session_id}...")
        stmt = select(models.Vacation).where(models.Vacation.session_id == target_session_id)
        vacation = (await session.execute(stmt)).scalar_one_or_none()
        
        if not vacation:
            print(f"❌ Error: session_id {target_session_id} not found in the vacations table.")
            await engine.dispose()
            return

        payload = {
            "id": vacation.id, "destination": vacation.destination, "origin": vacation.origin,
            "from_date": vacation.from_date.isoformat() if vacation.from_date else None,
            "to_date": vacation.to_date.isoformat() if vacation.to_date else None,
            "adults": vacation.adults, "children": vacation.children,
            "flight_price": vacation.flight_price, "flight_ccy": vacation.flight_ccy, "airport_name": vacation.airport_name,
            "accommodation_price": vacation.accommodation_price, "accommodation_ccy": vacation.accommodation_ccy,
            "accommodation_name": vacation.accommodation_name, "accommodation_address": vacation.accommodation_address,
            "itinerary_data": vacation.itinerary_data
        }

        print("🖨️ Spawning WeasyPrint document compilation task layer...")
        pdf_bytes = generate_itinerary_pdf(payload)
        
        output_name = f"itinerary_session_{target_session_id}.pdf"
        with open(output_name, "wb") as f:
            f.write(pdf_bytes)
        print(f"🎉 Success! Downloaded directly to local root path: ./{output_name}")

    await engine.dispose()

if __name__ == "__main__":
    # 💡 Simply update this ID here to test your generation pass
    TARGET_TEST_ID = 2
    asyncio.run(_run_local_test(TARGET_TEST_ID))
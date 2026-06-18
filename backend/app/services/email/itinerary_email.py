import smtplib
from email.message import EmailMessage
from app.core.config import settings
from app.core.logger import get_logger
from app.services.email.templates import get_vacation_blueprint_html

log = get_logger(__name__)

from app.core.logger import get_logger
from app.services.email.pdf_builder import generate_itinerary_pdf

log = get_logger(__name__)


async def send_vacation_blueprint_email(to_email: str, session_data: dict) -> bool:
    """
    Generates a vector-grade itinerary PDF, packages it as an unmodifiable MIME
    attachment, and dispatches a clean HTML cover letter via SMTP.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.error(
            "SMTP credentials missing from application environment configurations."
        )
        return False

    normalized_data = dict(session_data)
    if (
        "accommodation_price" in normalized_data
        and "accommodation_price" not in normalized_data
    ):
        normalized_data["accommodation_price"] = normalized_data.get(
            "accommodation_price"
        )
        normalized_data["accommodation_ccy"] = normalized_data.get("accommodation_ccy")
        normalized_data["accommodation_name"] = normalized_data.get(
            "accommodation_name"
        )
        normalized_data["accommodation_address"] = normalized_data.get(
            "accommodation_address"
        )
        normalized_data["accommodation_url"] = normalized_data.get("accommodation_url")

    msg = EmailMessage()
    destination = normalized_data.get("destination", "Your Destination")
    msg["Subject"] = f"Your Master Trip Blueprint for {destination} is Ready! 🌍"
    msg["From"] = f"TuRAG Travel Agent <{settings.SMTP_USER}>"
    msg["To"] = to_email

    html_cover_letter = get_vacation_blueprint_html(normalized_data)
    msg.add_alternative(html_cover_letter, subtype="html")

    try:
        log.info("🖨️ Compiling vector PDF blueprint for session context matching...")
        pdf_bytes = generate_itinerary_pdf(normalized_data)

        safe_filename = (
            f"TuRAG_Itinerary_{destination.replace(',', '').replace(' ', '_')}.pdf"
        )

        msg.add_attachment(
            pdf_bytes, maintype="application", subtype="pdf", filename=safe_filename
        )
    except Exception as pdf_err:
        log.error(f"Failed to compile PDF attachment layer: {pdf_err}", exc_info=True)
        return False

    try:
        log.info(
            f"🚀 Initializing secure SMTP socket link to {settings.SMTP_HOST}:{settings.SMTP_PORT}..."
        )
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        log.info(
            f"🎉 Success! Vacation blueprint email with PDF attachment dispatched to {to_email}"
        )
        return True
    except Exception as e:
        log.error(
            f"Failed to dispatch vacation blueprint email via SMTP: {e}", exc_info=True
        )
        return False

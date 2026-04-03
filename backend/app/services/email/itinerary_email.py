import smtplib
from email.message import EmailMessage
from app.core.config import settings
from app.core.logger import get_logger
from app.services.email.templates import get_vacation_blueprint_html

log = get_logger(__name__)

def send_vacation_blueprint_email(to_email: str, session_data: dict) -> bool:
    """Sends the final trip blueprint email. Returns True if successful."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.error("SMTP credentials missing.")
        return False

    msg = EmailMessage()
    msg['Subject'] = "Your Trip Blueprint is Ready! 🌍"
    msg['From'] = f"TuRAG <{settings.SMTP_USER}>"
    msg['To'] = to_email
    msg.add_alternative(get_vacation_blueprint_html(session_data), subtype='html')

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            log.info(f"Vacation blueprint email sent to {to_email}")
            return True
    except Exception as e:
        log.error(f"Failed to send vacation blueprint email: {e}")
        return False
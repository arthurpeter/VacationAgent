import smtplib
import jwt
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from app.core.config import settings
from app.core.logger import get_logger
from app.services.email.templates import get_verification_email_html

log = get_logger(__name__)

def create_verification_token(email: str) -> str:
    """Creates a 24-hour JWT token for email verification."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email, "type": "email_verification"}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_verification_token(token: str) -> str | None:
    """Decodes token and returns email if valid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        return payload.get("sub")
    except Exception:
        return None

def send_verification_email(to_email: str) -> bool:
    """Generates token and sends email. Returns True if successful."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.warning("SMTP credentials missing.")
        return False

    token = create_verification_token(to_email)
    
    frontend_url = "http://localhost:5173" 
    verification_link = f"{frontend_url}/verify-email?token={token}"
    log.info(f"Generated verification link for {to_email}: {verification_link}")

    msg = EmailMessage()
    msg['Subject'] = "Please Verify Your Email - TuRAG"
    msg['From'] = f"TuRAG <{settings.SMTP_USER}>"
    msg['To'] = to_email
    msg.add_alternative(get_verification_email_html(verification_link), subtype='html')

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            log.info(f"✅ Verification email sent to {to_email}")
            return True
    except Exception as e:
        log.error(f"❌ Failed to send verification email: {e}")
        return False
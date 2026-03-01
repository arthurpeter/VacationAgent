import smtplib
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from app.core.config import settings
from app.core.logger import get_logger
from app.services.email.templates import get_password_reset_email_html
from app.utils.security import is_token_revoked

log = get_logger(__name__)

def create_password_reset_token(email: str) -> str:
    """Creates a 1-hour JWT token for password reset with a unique JTI."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode = {
        "exp": expire, 
        "sub": email, 
        "type": "password_reset",
        "jti": uuid.uuid4().hex  # <-- Added a unique ID for blacklisting
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_password_reset_token(token: str) -> dict | None:
    """Decodes token, checks blacklist, and returns the full payload if valid."""
    try:
        # 1. Check if the token was already used and blacklisted
        if is_token_revoked(token):
            return None
            
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        if payload.get("type") != "password_reset":
            return None
            
        # Return the whole payload so we have access to the email, exp, and jti
        return payload
    except Exception:
        return None

def send_password_reset_email(to_email: str) -> bool:
    """Generates token and sends password reset email. Returns True if successful."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.warning("SMTP credentials missing.")
        return False

    token = create_password_reset_token(to_email)
    
    frontend_url = "http://localhost:5173" 
    reset_link = f"{frontend_url}/reset-password?token={token}"
    log.info(f"Generated password reset link for {to_email}: {reset_link}")

    msg = EmailMessage()
    msg['Subject'] = "Reset Your Password - TuRAG"
    msg['From'] = f"TuRAG <{settings.SMTP_USER}>"
    msg['To'] = to_email
    msg.add_alternative(get_password_reset_email_html(reset_link), subtype='html')

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            log.info(f"✅ Password reset email sent to {to_email}")
            return True
    except Exception as e:
        log.error(f"❌ Failed to send password reset email: {e}")
        return False

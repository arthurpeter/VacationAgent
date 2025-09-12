"""
Authentication configuration and setup using AuthX.
"""
from authx import AuthX, AuthXConfig
from app.core.config import settings
from app.utils.security import is_token_revoked

# Configure AuthX
config = AuthXConfig(
    JWT_ALGORITHM=settings.JWT_ALGORITHM,
    JWT_SECRET_KEY=settings.JWT_SECRET_KEY,  # In production, use a secure key and store it in environment variables
    # Configure token locations
    JWT_TOKEN_LOCATION=["headers", "cookies"],
    # Header settings
    JWT_HEADER_TYPE="Bearer",
    # Token expiration settings
    JWT_ACCESS_TOKEN_EXPIRES=60 * 15,  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES=60 * 60 * 24 * 30,  # 30 days
    # Cookie settings
    JWT_REFRESH_COOKIE_NAME="refresh_token_cookie",
    JWT_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT=True,  # Enable CSRF protection
    JWT_COOKIE_SAMESITE="lax",
    JWT_COOKIE_DOMAIN=None,
    # CSRF settings 
    JWT_REFRESH_CSRF_COOKIE_NAME="csrf_refresh_token",
    JWT_REFRESH_CSRF_HEADER_NAME="X-CSRF-TOKEN-Refresh",
)

# Create AuthX instance
auth = AuthX(config=config)

@auth.set_callback_token_blocklist
def token_blocklist_callback(token: str) -> bool:
    return is_token_revoked(token)

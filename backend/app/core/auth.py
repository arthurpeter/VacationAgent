"""
Authentication configuration and setup using AuthX.
"""
from authx import AuthX, AuthXConfig, TokenPayload
from fastapi import Request
from app.core.config import settings
from app.utils.security import is_token_revoked

config = AuthXConfig(
    JWT_ALGORITHM=settings.JWT_ALGORITHM,
    JWT_SECRET_KEY=settings.JWT_SECRET_KEY,  # In production, use a secure key and store it in environment variables
    JWT_TOKEN_LOCATION=["headers", "cookies"],
    JWT_HEADER_TYPE="Bearer",
    JWT_ACCESS_TOKEN_EXPIRES=60 * 15,  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES=60 * 60 * 24 * 30,  # 30 days
    JWT_REFRESH_COOKIE_NAME="refresh_token_cookie",
    JWT_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT=True,  # Enable CSRF protection
    JWT_COOKIE_SAMESITE="lax",
    JWT_COOKIE_DOMAIN=None,
    JWT_REFRESH_CSRF_COOKIE_NAME="csrf_refresh_token",
    JWT_REFRESH_CSRF_HEADER_NAME="X-CSRF-TOKEN-Refresh",
)

auth = AuthX(config=config)

@auth.set_callback_token_blocklist
async def token_blocklist_callback(token: str) -> bool:
    return await is_token_revoked(token)


async def access_token_header(request: Request) -> TokenPayload:
    """
    Extrage și verifică Access Token-ul EXCLUSIV din Header-ul Authorization.
    Previne coliziunea cu alte token-uri prezente în cookies.
    """
    token_str = await auth.get_access_token_from_request(request, locations=["headers"])
    return auth.verify_token(token_str, verify_csrf=False)

async def refresh_token_cookie(request: Request) -> TokenPayload:
    """
    Extrage și verifică Refresh Token-ul EXCLUSIV din Cookie-ul HttpOnly.
    Ignoră orice token de tip Access prezent în Header-ul Authorization.
    """
    token_str = await auth.get_refresh_token_from_request(request, locations=["cookies"])
    return auth.verify_token(token_str)
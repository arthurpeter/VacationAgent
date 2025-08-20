"""
Authentication configuration and setup using AuthX.
"""
from authx import AuthX, AuthXConfig
from app.core.config import settings
from app.models.blacklist_token import BlacklistToken
from app.core.database import SessionLocal

# Configure AuthX
config = AuthXConfig()
config.JWT_SECRET_KEY = settings.JWT_SECRET_KEY
config.JWT_ALGORITHM = settings.JWT_ALGORITHM
config.JWT_TOKEN_LOCATION = ["headers", "json"]

# Create AuthX instance
auth = AuthX(config=config)

@auth.set_callback_token_blocklist
def is_token_revoked(token: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(BlacklistToken).filter_by(token=token).first() is not None
    finally:
        db.close()

"""
Authentication configuration and setup using AuthX.
"""
from authx import AuthX, AuthXConfig
from app.core.config import settings
from app.utils.security import is_token_revoked

# Configure AuthX
config = AuthXConfig()
config.JWT_SECRET_KEY = settings.JWT_SECRET_KEY
config.JWT_ALGORITHM = settings.JWT_ALGORITHM

# Create AuthX instance
auth = AuthX(config=config)

@auth.set_callback_token_blocklist
def token_blocklist_callback(token: str) -> bool:
    return is_token_revoked(token)

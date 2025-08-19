"""
Authentication configuration and setup using AuthX.
"""
from authx import AuthX, AuthXConfig
from app.core.config import settings

# Configure AuthX
config = AuthXConfig()
config.JWT_SECRET_KEY = settings.JWT_SECRET_KEY
config.JWT_ALGORITHM = settings.JWT_ALGORITHM

# Create AuthX instance
auth = AuthX(config=config)

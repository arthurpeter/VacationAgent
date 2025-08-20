from sqlalchemy import Column, String, DateTime
from app.core.database import Base

class BlacklistToken(Base):
    __tablename__ = "blacklist_tokens"
    token = Column(String, primary_key=True, index=True)
    expires_at = Column(DateTime, nullable=False)
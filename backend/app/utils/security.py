from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.blacklist_token import BlacklistToken
from app.core.database import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def blacklist_token(db: Session, token: str, expires_at: datetime):
    db_token = BlacklistToken(token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()

def is_token_revoked(token: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(BlacklistToken).filter_by(token=token).first() is not None
    finally:
        db.close()

def cleanup_blacklist(db: Session):
    db.query(BlacklistToken).filter(BlacklistToken.expires_at < datetime.now()).delete()
    db.commit()


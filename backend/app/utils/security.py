from datetime import datetime
import bcrypt
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.blacklist_token import BlacklistToken
from app.core.database import SessionLocal

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

async def blacklist_token(db: AsyncSession, token: str, expires_at: datetime):
    db_token = BlacklistToken(token=token, expires_at=expires_at)
    db.add(db_token)
    await db.commit()

async def is_token_revoked(token: str) -> bool:
    """Check if a JWT token is blacklisted"""
    async with SessionLocal() as db:
        payload = jwt.decode(
            token, 
            options={"verify_signature": False, "verify_exp": False}
        )
        jti = payload.get("jti")
        
        if not jti:
            return False
            
        stmt = select(BlacklistToken).filter_by(token=jti)
        result = await db.execute(stmt)
        
        return result.scalars().first() is not None



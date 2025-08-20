"""Authentication router using AuthX."""
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
import jwt
from pydantic import BaseModel
from authx import RequestToken
from app.core.auth import auth
from app.core.database import get_db
from app import models, schemas, utils
from app.core.config import settings
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = utils.security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class LoginForm(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginForm, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not utils.security.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access = auth.create_access_token(uid=user.id)
    refresh = auth.create_refresh_token(uid=user.id)
    return {"access_token": access, "refresh_token": refresh}
    

@router.post("/refresh")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    # 1) get header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token_str = auth_header.split(" ", 1)[1].strip()

    # 2) decode & validate (PyJWT)
    try:
        payload = jwt.decode(token_str, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # 3) ensure it's a refresh token and has subject
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token is not a refresh token")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Token missing subject")
    
    if utils.security.is_token_revoked(token_str):
        raise HTTPException(status_code=401, detail="Token is revoked")

    new_access = auth.create_access_token(uid=uid)
    new_refresh = auth.create_refresh_token(uid=uid)
    # Blacklist the old token
    expires_at = datetime.datetime.fromtimestamp(payload.get("exp"))
    utils.security.blacklist_token(db=next(get_db()), token=token_str, expires_at=expires_at)
    print(payload)
    return {
        "access_token": new_access,
        "refresh_token": new_refresh
    }

"""Authentication router using AuthX."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from authx import RequestToken
from app.core.auth import auth
from app.core.database import get_db
from app import models, schemas, utils
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginForm(BaseModel):
    username: str
    password: str

class RefreshForm(BaseModel):
    refresh_token: str


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

@router.post("/login")
def login(data: LoginForm):
    if data.username == "user" and data.password == "pass":
        access = auth.create_access_token(uid=data.username)
        refresh = auth.create_refresh_token(uid=data.username)
        return {"access_token": access, "refresh_token": refresh}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/refresh")
async def refresh(
    request, data: RefreshForm = None, token: RequestToken = Depends(auth.get_token_from_request(type="refresh", optional=True))
):
    try:
        payload = await auth.refresh_token_required(request)
    except Exception:
        if not (data and data.refresh_token):
            raise HTTPException(status_code=401, detail="Refresh token missing")
        payload = auth.verify_token(token=data.refresh_token, verify_type=True, type="refresh")
    new_access = auth.create_access_token(uid=payload.sub)
    return {"access_token": new_access}

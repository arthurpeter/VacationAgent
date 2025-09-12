"""Authentication router using AuthX."""
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from app.core.auth import auth
from app.core.database import get_db
from app import models, schemas, utils
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
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
async def login(data: LoginForm, response: Response, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if not user or not utils.security.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access = auth.create_access_token(uid=user.id)
    refresh = auth.create_refresh_token(uid=user.id)
    
    print("access:", access)
    print("refresh:", refresh)

    # Clear any existing cookies
    auth.unset_cookies(response)

    # Set refresh token cookie using AuthX method - this will automatically set CSRF cookie too
    auth.set_refresh_cookies(refresh, response, max_age=60 * 60 * 24 * 30)

    return {"access_token": access}
    

@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    try:    
        request_token = await auth.get_refresh_token_from_request(request)
        payload = auth.verify_token(request_token)

        # Blacklist old refresh token
        utils.security.blacklist_token(db=db, token=payload.jti, expires_at=payload.exp)

        # Clear existing cookies
        auth.unset_cookies(response)

        # Create new tokens
        new_access = auth.create_access_token(uid=payload.sub)
        new_refresh = auth.create_refresh_token(uid=payload.sub)

        # Set new refresh token cookie - this will automatically set CSRF cookie too
        auth.set_refresh_cookies(new_refresh, response)

        return {
            "access_token": new_access,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from e

from fastapi import Request

class LogoutForm(BaseModel):
    refresh_token: str

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        access_token = await auth.get_access_token_from_request(request)
        request_token = await auth.get_refresh_token_from_request(request)
    
        access_payload = auth.verify_token(access_token)
        request_payload = auth.verify_token(request_token)

        # Blacklist access token using the token's jti (unique identifier)
        utils.security.blacklist_token(db=db, token=access_payload.jti, expires_at=access_payload.exp)

        # Blacklist refresh token using the token's jti (unique identifier)
        utils.security.blacklist_token(db=db, token=request_payload.jti, expires_at=request_payload.exp)
        
        auth.unset_cookies(response)

        return {"detail": "Successfully logged out"}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid token") from e

@router.post("/validate", dependencies=[Depends(auth.access_token_required)])
async def validate_token():
    return {"message" : "Token is valid"}

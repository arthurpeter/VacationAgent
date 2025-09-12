"""Authentication router using AuthX."""
from authx import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from app.core.auth import auth
from app.core.database import get_db
from app import models, schemas, utils
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    hashed_password = utils.security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class LoginForm(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginForm, response: Response, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not utils.security.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access = auth.create_access_token(uid=user.id)
    refresh = auth.create_refresh_token(uid=user.id)

    # Clear any existing cookies
    auth.unset_cookies(response)

    # Set refresh token cookie using AuthX method - this will automatically set CSRF cookie too
    auth.set_refresh_cookies(refresh, response, max_age=60 * 60 * 24 * 30)

    return {"access_token": access}
    

@router.post("/refresh")
async def refresh_token(
    response: Response,
    token: TokenPayload = Depends(auth.refresh_token_required),
    db: Session = Depends(get_db)
):
    try:    
        # Blacklist old refresh token
        utils.security.blacklist_token(db=db, token=token.jti, expires_at=token.exp)

        # Clear existing cookies
        auth.unset_cookies(response)

        # Create new tokens
        new_access = auth.create_access_token(uid=token.sub)
        new_refresh = auth.create_refresh_token(uid=token.sub)

        # Set new refresh token cookie - this will automatically set CSRF cookie too
        auth.set_refresh_cookies(new_refresh, response)

        return {
            "access_token": new_access,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from e

class LogoutForm(BaseModel):
    refresh_token: str

@router.post("/logout")
async def logout(
    response: Response,
    access_token: TokenPayload = Depends(auth.access_token_required),
    refresh_token: TokenPayload = Depends(auth.refresh_token_required),
    db: Session = Depends(get_db),
):
    try:
        # Blacklist access token using the token's jti (unique identifier)
        utils.security.blacklist_token(db=db, token=access_token.jti, expires_at=access_token.exp)

        # Blacklist refresh token using the token's jti (unique identifier)
        utils.security.blacklist_token(db=db, token=refresh_token.jti, expires_at=refresh_token.exp)

        auth.unset_cookies(response)

        return {"detail": "Successfully logged out"}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid token") from e

@router.post("/validate", dependencies=[Depends(auth.access_token_required)])
async def validate_token():
    return {"message" : "Token is valid"}

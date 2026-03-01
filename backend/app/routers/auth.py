"""Authentication router using AuthX."""
from authx import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from pydantic import BaseModel
from app.core.auth import auth
from app.core.database import get_db
from app import models, schemas, utils
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.services.email.confirm_email import send_verification_email, decode_verification_token
from app.services.email.password_reset import send_password_reset_email, decode_password_reset_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.User)
async def register_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        if not db_user.is_verified:
            db.delete(db_user)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail="Email already registered")
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    hashed_password = utils.security.get_password_hash(user.password)
    background_tasks.add_task(send_verification_email, user.email)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class ResendEmailRequest(BaseModel):
    email: str

@router.post("/resend-verification")
async def resend_verification(
    data: ResendEmailRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        return {"message": "If the email is registered, a link has been sent."}
    if user.is_verified:
        return {"message": "Email is already verified."}
        
    background_tasks.add_task(send_verification_email, user.email)
    return {"message": "Verification email resent."}

@router.post("/verify-email")
async def verify_email(token: str, response: Response, db: Session = Depends(get_db)):
    """Verifies the token, marks user as verified, and logs them in."""
    email = decode_verification_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.is_verified:
        user.is_verified = True
        db.commit()
    
    access = auth.create_access_token(uid=user.id)
    refresh = auth.create_refresh_token(uid=user.id)
    auth.unset_cookies(response)
    auth.set_refresh_cookies(refresh, response, max_age=60 * 60 * 24 * 30)
    
    return {"access_token": access, "message": "Email verified successfully"}

class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if user:
        background_tasks.add_task(send_password_reset_email, user.email)
        
    return {"message": "If that email is in our system, we have sent a password reset link."}

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    payload = decode_password_reset_token(data.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid, expired, or already used password reset link")
        
    email = payload.get("sub")
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if utils.security.verify_password(data.new_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Your new password cannot be the same as your old password.")
        
    user.hashed_password = utils.security.get_password_hash(data.new_password)
    
    exp_timestamp = payload.get("exp")
    jti = payload.get("jti")
    if jti and exp_timestamp:
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc).replace(tzinfo=None)
        utils.security.blacklist_token(db=db, token=jti, expires_at=expires_at)

    db.commit()
    
    return {"message": "Password has been reset successfully. You can now log in."}

class LoginForm(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginForm, response: Response, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not utils.security.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Login failed. Please check your credentials.")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please check your inbox.")
    
    access = auth.create_access_token(uid=user.id)
    refresh = auth.create_refresh_token(uid=user.id)

    auth.unset_cookies(response)

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

        auth.unset_cookies(response)

        new_access = auth.create_access_token(uid=token.sub)
        new_refresh = auth.create_refresh_token(uid=token.sub)

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
        utils.security.blacklist_token(db=db, token=access_token.jti, expires_at=access_token.exp)

        utils.security.blacklist_token(db=db, token=refresh_token.jti, expires_at=refresh_token.exp)

        auth.unset_cookies(response)

        return {"detail": "Successfully logged out"}
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid token") from e

@router.post("/validate", dependencies=[Depends(auth.access_token_required)])
async def validate_token():
    return {"message" : "Token is valid"}

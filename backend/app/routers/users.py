from authx import RequestToken
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import auth
from app import models, schemas
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=schemas.User)
async def read_current_user(
    db: Session = Depends(get_db),
    token: RequestToken = Depends(auth.access_token_required)
):
    user = db.query(models.User).filter(models.User.id == token.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
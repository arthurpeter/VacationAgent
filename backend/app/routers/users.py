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

@router.patch("/me", response_model=schemas.User)
async def update_current_user(
    update_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    token: RequestToken = Depends(auth.access_token_required)
):
    """Update user preferences and account details."""
    user = db.query(models.User).filter(models.User.id == token.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/companions", response_model=schemas.TravelCompanionResponse)
async def add_travel_companion(
    companion_data: schemas.TravelCompanionCreate,
    db: Session = Depends(get_db),
    token: RequestToken = Depends(auth.access_token_required)
):
    """Add a new companion to the user's vault."""
    new_companion = models.TravelCompanion(
        user_id=token.sub,
        **companion_data.model_dump()
    )
    db.add(new_companion)
    db.commit()
    db.refresh(new_companion)
    return new_companion

@router.delete("/me/companions/{companion_id}")
async def remove_travel_companion(
    companion_id: str,
    db: Session = Depends(get_db),
    token: RequestToken = Depends(auth.access_token_required)
):
    """Remove a companion from the vault."""
    companion = db.query(models.TravelCompanion).filter(
        models.TravelCompanion.id == companion_id,
        models.TravelCompanion.user_id == token.sub
    ).first()
    
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
        
    db.delete(companion)
    db.commit()
    return {"detail": "Companion removed successfully"}
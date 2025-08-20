from fastapi import APIRouter, Depends
from app.core.auth import auth

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", dependencies=[Depends(auth.access_token_required)])
async def read_current_user():
    return {"user": "You are authenticated!"}
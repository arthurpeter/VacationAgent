"""User schemas for AuthX authentication."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class TravelCompanionBase(BaseModel):
    name: str
    date_of_birth: datetime
    description: Optional[str] = None
    is_infant_on_lap: Optional[bool] = False

class TravelCompanionCreate(TravelCompanionBase):
    pass

class TravelCompanionResponse(TravelCompanionBase):
    id: str
    user_id: str

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str
    confirm_password: str

class UserUpdate(BaseModel):
    """Schema for updating user preferences and details."""
    currency_preference: Optional[str] = None
    home_airports: Optional[List[str]] = None
    date_of_birth: Optional[datetime] = None
    user_description: Optional[str] = None

class User(UserBase):
    id: str
    currency_preference: Optional[str] = None
    home_airports: Optional[List[str]] = []
    date_of_birth: Optional[datetime] = None
    user_description: Optional[str] = None
    companions: Optional[List[TravelCompanionResponse]] = []

    class Config:
        from_attributes = True

"""User schemas for AuthX authentication."""
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str

class User(UserBase):
    id: str

    class Config:
        from_attributes = True

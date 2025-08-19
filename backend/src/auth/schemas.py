"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user response (without password)."""
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True

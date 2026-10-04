from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Jane Doe")
    email: EmailStr = Field(..., example="jane.doe@example.com")
    age: int = Field(..., ge=0, le=130, example=24)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(None, ge=0, le=130)


class UserResponse(UserBase):
    id: UUID

    class Config:
        from_attributes = True
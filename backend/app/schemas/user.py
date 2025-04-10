from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Union
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None


class UserCreate(UserBase):
    google_id: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: str
    google_id: str
    is_active: bool
    created_at: Union[datetime, str]
    updated_at: Union[datetime, str]

    model_config = {
        "from_attributes": True
    }


class UserResponse(UserBase):
    id: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class GoogleAuthRequest(BaseModel):
    token: str


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    exp: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

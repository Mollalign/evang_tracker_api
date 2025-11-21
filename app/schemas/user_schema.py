from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone
from uuid import UUID
from app.models.user import UserRole

class UserCreateSchema(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str | None = None
    role: UserRole = UserRole.evangelist
    password: str
    is_active: bool = True

class UserSchema(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    phone_number: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr    

class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str
 

class ResetPasswordResponse(BaseModel):
    message: str = "Password reset successful"


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    old_password: str
    password: str
    confirm_password: str


class ChangePasswordResponse(BaseModel):
    message: str = "Password changed successfully"


class UserRoleUpdateRequest(BaseModel):
    role: UserRole    

class UserStatusUpdateRequest(BaseModel):
    is_active: bool    
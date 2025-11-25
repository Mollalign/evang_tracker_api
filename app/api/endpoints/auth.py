from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_current_user
from app.models.user import User

from app.core.database import get_db
from app.schemas.user_schema import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    UserCreateSchema,
    UserSchema,
    ForgotPasswordRequest
)
from app.services.auth_service import AuthService
from app.models.user import UserRole


router = APIRouter(tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


# Register router
@router.post("/register", response_model=UserSchema)
async def register_user(
  request: UserCreateSchema,
  service: AuthService = Depends(get_auth_service)
):
   # Only allow evangelist role registration
   if request.role == UserRole.admin:
       raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="Admin accounts cannot be created through registration. Please contact system administrator."
       )
   return await service.register_user(request)


# login router
@router.post("/login", response_model=LoginResponse)
async def login(
  request: LoginRequest,
  response: Response,
  service: AuthService = Depends(get_auth_service),
):
    user = await service.authenticate_user(request)
    tokens = service.issue_token_pair(str(user.id))


    response.set_cookie(
        key="accessToken",
        value=tokens["access_token"], 
        httponly=True,
        secure=False,  
        samesite="None",
        path="/"
    )

    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=user
    )


# refresh token
@router.post("/refresh-token", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
):
    tokens = await service.rotate_refresh_token(request)
    return RefreshTokenResponse(**tokens)


# forget password
@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service)
):
    await service.send_forgot_password_email(request)
    return {"message": "Reset link sent to your email"}


# Reset password
@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service)
):
    await service.reset_password_service(request)
    return {"message": "Password reset successful"}


@router.get("/me", response_model=UserSchema)
async def current_user(
   user: User = Depends(get_current_user)
):
    return UserSchema(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
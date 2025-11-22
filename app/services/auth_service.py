from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.password_reset import PasswordResetToken
from app.utils.send_mail import send_email

from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.models.user import User, UserRole
from app.schemas.user_schema import (
    LoginRequest,
    ChangePasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    UserCreateSchema,
    UserSchema,
    ForgotPasswordRequest
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # get user by email 
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    

    # register
    async def register_user(self, payload: UserCreateSchema) -> UserSchema:
        # check if user already exist
        if await self._get_user_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exist"
            )
        
        new_user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone_number=payload.phone_number,
            role=UserRole.evangelist,
            password_hash=get_password_hash(payload.password),
            is_active=payload.is_active,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return UserSchema.model_validate(new_user, from_attributes=True)
    

    # authenticate user
    async def authenticate_user(self, payload: LoginRequest) -> User:
        user = await self._get_user_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Credentials",
            )
        
        return user
    

    # issue token pair
    @staticmethod
    def issue_token_pair(user_id: str) -> dict[str, str]:
        return {
            "access_token": create_access_token(user_id),
            "refresh_token": create_refresh_token(user_id)
        }
    
    # refresh token service
    async def rotate_refresh_token(self, payload: RefreshTokenRequest) -> dict[str, str]:
        token_payload = verify_token(
            payload.refresh_token, token_type=TOKEN_TYPE_REFRESH
        )
        if token_payload is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token",
            )
        return self.issue_token_pair(token_payload.get("sub"))
    

    # Forget password
    async def send_forgot_password_email(self, payload: ForgotPasswordRequest):
        # 1. Check if user exists
        user = await self._get_user_by_email(payload.email)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail="User not found"
            )

        # 2. Generate and store token
        token = PasswordResetToken.generate(user.email)
        await self.db.merge(token)
        await self.db.commit()

        reset_link = f"https://yourfrontend.com/reset-password?token={token.token}"

        html = f"""
            <h2>Password Reset Request</h2>
            <p>Hello {user.full_name},</p>
            <p>Click the button below to reset your password:</p>
            <a href="{reset_link}" 
            style="padding: 10px 20px; background: #007bff; color: #fff; text-decoration:none; border-radius: 5px;">
                Reset Password
            </a>
            <p>This link expires in <strong>15 minutes</strong>.</p>
        """

        send_email(user.email, "Password Reset", html)


    # Reset password
    async def reset_password_service(self, payload: ResetPasswordRequest):

        # 1. Check password confirmation
        if payload.password != payload.confirm_password:
            raise HTTPException(400, "Passwords do not match")

        # 2. Find token in DB
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token == payload.token
        )
        reset_token_result = await self.db.execute(stmt)
        reset_token = reset_token_result.scalars().first()

        if not reset_token:
            raise HTTPException(400, "Invalid or expired token")

        # 3. Check expiration
        if reset_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(400, "Token has expired")

        # 4. Fetch user by email (since PasswordResetToken uses email as primary key)
        user = await self._get_user_by_email(reset_token.email)

        if not user:
            raise HTTPException(404, "User not found")

        # 5. Update password
        user.password_hash = get_password_hash(payload.password)

        # 6. One-time token → remove it
        await self.db.delete(reset_token)

        # 7. Save changes
        await self.db.commit()

        

        
        
        


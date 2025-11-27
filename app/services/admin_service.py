from typing import List
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user_schema import (
    AdminUserCreateSchema,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
)


class AdminService:
    """Admin-focused operations such as user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_user(self, user_in: AdminUserCreateSchema) -> User:
        result = await self.db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        new_user = User(
            full_name=user_in.full_name,
            email=user_in.email,
            phone_number=user_in.phone_number,
            role=user_in.role,
            password_hash=get_password_hash(user_in.password),
            is_active=user_in.is_active,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def _get_user_or_raise(self, user_id: UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_user_role(
        self, user_id: UUID, role_update: UserRoleUpdateRequest
    ) -> User:
        user = await self._get_user_or_raise(user_id)
        user.role = role_update.role
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_status(
        self, user_id: UUID, status_update: UserStatusUpdateRequest
    ) -> User:
        user = await self._get_user_or_raise(user_id)
        user.is_active = status_update.is_active
        await self.db.commit()
        await self.db.refresh(user)
        return user


from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import require_admin
from app.models.user import User
from app.schemas.user_schema import (
    UserSchema, 
    AdminUserCreateSchema, 
    UserRoleUpdateRequest, 
    UserStatusUpdateRequest
)
from app.services.admin_service import AdminService

router = APIRouter()

def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db)

@router.get("/users", response_model=List[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    """
    List all users.
    Only accessible by admins.
    """
    return await service.list_users(skip, limit)

@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: AdminUserCreateSchema,
    current_user: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    """
    Create a new user (admin or evangelist).
    Only accessible by admins.
    """
    return await service.create_user(user_in)

@router.patch("/users/{user_id}/role", response_model=UserSchema)
async def update_user_role(
    user_id: UUID,
    role_update: UserRoleUpdateRequest,
    current_user: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    """
    Update user role.
    Only accessible by admins.
    """
    return await service.update_user_role(user_id, role_update)

@router.patch("/users/{user_id}/status", response_model=UserSchema)
async def update_user_status(
    user_id: UUID,
    status_update: UserStatusUpdateRequest,
    current_user: User = Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    """
    Update user active status.
    Only accessible by admins.
    """
    return await service.update_user_status(user_id, status_update)

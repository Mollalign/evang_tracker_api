from fastapi import HTTPException, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Annotated, AsyncGenerator    
from sqlalchemy import select       
from app.core.database import get_db
from app.core.security import verify_token, get_token_remaining_time
from app.models.user import User, UserRole
from app.models.outreachReport import OutreachReport
from uuid import UUID

async def get_token_from_header(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Get the token from the header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return authorization.split(" ")[1]  

async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(get_token_from_header)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current user from the database."""
    payload = verify_token(token)   
    if payload is None:         
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")    
    user = await db.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get the database session."""
    async with get_db() as session:
        yield session

async def _get_token_remaining_time(
    token: Annotated[str, Depends(get_token_from_header)],
) -> int:
    """Get the remaining time for the token."""
    return get_token_remaining_time(token)

async def get_current_user_from_token(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current user from the token."""
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_user_from_request(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Get the current user from the request."""
    token = get_token_from_header(request.headers.get("Authorization"))
    return await get_current_user_from_token(token, db)

async def get_current_user_from_request_with_token(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Tuple[User, str]:
    """Get the current user from the request with token."""
    token = get_token_from_header(request.headers.get("Authorization"))
    user = await get_current_user_from_token(token, db)
    return user, token

async def get_current_user_from_request_without_token(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Tuple[User, None] | Tuple[None, str] | Tuple[None, None] | None:
    """Get the current user from the request without token."""
    user = await get_current_user_from_request(request, db)
    return user, None

async def get_current_user_from_request_without_token_with_token(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Tuple[User, str]:
    """Get the current user from the request without token with token."""
    return await get_current_user_from_request_with_token(request, db)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user

async def require_evangelist(current_user: User = Depends(get_current_user)) -> User:
    """Require user to be an evangelist"""
    if current_user.role != UserRole.evangelist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Evangelist privileges required",
        )
    return current_user

async def require_any_authenticated_user(current_user: User = Depends(get_current_user)) -> User:
    """Just verify user is authenticated (already done by get_current_user)"""
    return current_user


# verify report ownership
async def verify_report_ownership(
   report_id: UUID,
   current_user: User,
   db: AsyncSession     
) -> OutreachReport:
    """
        Verify user owns the report or is admin.
        - Admins can access any report
        - Evangelists can only access their own reports
    """
    
    result = await db.execute(
        select(OutreachReport).where(OutreachReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Admins can access any report
    if current_user.role == UserRole.admin:
        return report
    
    # Evangelists can only access their own reports
    if report.evangelist_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own reports"
        )
    
    return report

     
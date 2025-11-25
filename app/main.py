import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy.dialects.postgresql.asyncpg import AsyncAdapt_asyncpg_dbapi

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import DatabaseManager, AsyncSessionLocal, invalidate_connection_pool
from app.api.endpoints.auth import router as auth_router

logger = logging.getLogger(__name__)


class InvalidCachedStatementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically handle InvalidCachedStatementError.
    This error occurs when database schema changes (e.g., after migrations)
    while the server is running, invalidating cached prepared statements.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Check if it's the InvalidCachedStatementError
            is_cached_error = (
                isinstance(exc, AsyncAdapt_asyncpg_dbapi.InvalidCachedStatementError) or
                (hasattr(exc, '__cause__') and 
                 isinstance(exc.__cause__, AsyncAdapt_asyncpg_dbapi.InvalidCachedStatementError)) or
                (hasattr(exc, 'orig') and 
                 isinstance(exc.orig, AsyncAdapt_asyncpg_dbapi.InvalidCachedStatementError))
            )
            
            if is_cached_error:
                logger.warning(
                    "InvalidCachedStatementError detected. "
                    "Invalidating connection pool and retrying request..."
                )
                try:
                    # Invalidate the connection pool
                    await invalidate_connection_pool()
                    # Retry the request once
                    response = await call_next(request)
                    return response
                except Exception as retry_exc:
                    logger.error(f"Error after invalidating pool: {retry_exc}")
                    return JSONResponse(
                        status_code=500,
                        content={
                            "detail": (
                                "Database schema changed. Please restart the server "
                                "or call POST /admin/invalidate-pool endpoint."
                            )
                        }
                    )
            # Re-raise if it's not the cached statement error
            raise


app = FastAPI(title="Evangelism App")

app.add_middleware(InvalidCachedStatementMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# check the api health
@app.get("/health")
async def health():
    db_ok = await DatabaseManager.health_check()
    return {"database": db_ok, "status": "ok" if db_ok else "error"}


@app.post("/admin/invalidate-pool")
async def invalidate_pool():
    """
    Invalidate the database connection pool.
    Call this endpoint after running Alembic migrations to clear cached prepared statements.
    This fixes the InvalidCachedStatementError that occurs after schema changes.
    """
    await invalidate_connection_pool()
    return {"message": "Connection pool invalidated successfully"}


# all routes 
app.include_router(auth_router, prefix="/api/auth")



import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # 8000 fallback for local
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)

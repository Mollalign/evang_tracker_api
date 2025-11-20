import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import DatabaseManager, AsyncSessionLocal

logger = logging.getLogger(__name__)


app = FastAPI(title="Evangelism App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    db_ok = await DatabaseManager.health_check()
    return {"database": db_ok, "status": "ok" if db_ok else "error"}


# app.include_router(auth_router, prefix="/api/auth")
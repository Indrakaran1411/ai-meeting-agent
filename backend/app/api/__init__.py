from fastapi import APIRouter
from app.api.v1.meetings import router as meetings_router

# Consolidated API v1 router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(meetings_router)

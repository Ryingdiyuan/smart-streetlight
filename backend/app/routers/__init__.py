from fastapi import APIRouter

from app.routers import devices, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(devices.router)

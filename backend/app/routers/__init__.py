from fastapi import APIRouter

from app.routers import agent, alarms, auth, commands, devices, health, light_data, simulator, thresholds

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(devices.router)
api_router.include_router(light_data.router)
api_router.include_router(thresholds.router)
api_router.include_router(commands.router)
api_router.include_router(alarms.router)
api_router.include_router(agent.router)
api_router.include_router(auth.router)
api_router.include_router(simulator.router)

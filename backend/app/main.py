from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.mqtt.client import mqtt_client
from app.routers import api_router
from app.tasks.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.mqtt_enabled:
        mqtt_client.start()
    if settings.scheduler_enabled:
        scheduler.start()
    yield
    if settings.scheduler_enabled:
        scheduler.shutdown(wait=False)
    if settings.mqtt_enabled:
        mqtt_client.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="智慧路灯节能系统后端服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }

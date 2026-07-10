"""Print users from the database configured in backend/.env."""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.device import Device
from app.models.user import User


def mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


db = SessionLocal()
try:
    print("=== Active database ===")
    print(f"Host: {settings.mysql_host}:{settings.mysql_port}")
    print(f"Database: {settings.mysql_database}")
    print(f"User: {settings.mysql_user}")
    print(f"Password: {mask(settings.mysql_password)}")
    print("")
    print("=== Users ===")
    users = db.query(User).order_by(User.id.asc()).all()
    for user in users:
        print(f"ID: {user.id}, username: {user.username}, role: {user.role}, active: {user.is_active}")
    if not users:
        print("(no users)")
    print("")
    print("=== Devices ===")
    devices = db.query(Device).order_by(Device.id.asc()).limit(20).all()
    for device in devices:
        print(
            f"ID: {device.id}, code: {device.device_code}, "
            f"name: {device.device_name}, status: {device.status}"
        )
    if not devices:
        print("(no devices)")
finally:
    db.close()

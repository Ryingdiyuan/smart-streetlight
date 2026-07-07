"""临时启动，无 reload 版，同时初始化数据"""
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from app.core import config, database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
DB_FILE = backend_dir / "temp_db.sqlite3"
SQLITE_URL = f"sqlite:///{str(DB_FILE).replace(os.sep, '/')}"
database.engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
database.SessionLocal = sessionmaker(
    bind=database.engine, autoflush=False, autocommit=False, future=True
)
config.settings.mqtt_enabled = False
config.settings.scheduler_enabled = False

from app.core.database import Base
from app.models import device, light_data, threshold_config, control_log, alarm_log, user
from app.models.device import Device
from app.models.threshold_config import ThresholdConfig
from app.models.light_data import LightData
from app.models.control_log import ControlLog
from app.models.alarm_log import AlarmLog
from app.models.user import User
from app.core.security import hash_password
from datetime import datetime, timedelta
import random

# 创建表结构
Base.metadata.create_all(bind=database.engine)

db = database.SessionLocal()
try:
    if db.query(User).count() == 0:
        print("[*] 创建用户 admin / admin123")
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin)

        devices_data = [
            {"code": "SL-001", "name": "东门入口路灯", "loc": "学校东门入口", "status": "online"},
            {"code": "SL-002", "name": "图书馆门口", "loc": "图书馆正门", "status": "online"},
            {"code": "SL-003", "name": "教学楼C栋", "loc": "第三教学楼前", "status": "offline"},
            {"code": "SL-004", "name": "学生宿舍区", "loc": "一号学生公寓", "status": "online"},
            {"code": "SL-005", "name": "体育场入口", "loc": "主体育场入口", "status": "online"}
        ]
        created_devices = []
        for d in devices_data:
            dev = Device(
                device_code=d["code"],
                device_name=d["name"],
                location=d["loc"],
                status=d["status"],
            )
            db.add(dev)
            created_devices.append(dev)
        db.commit()

        for dev in created_devices:
            db.refresh(dev)
            th = ThresholdConfig(
                device_id=dev.id,
                low_threshold=100,
                high_threshold=300,
                enabled=True,
            )
            db.add(th)

        now = datetime.utcnow()
        for dev in created_devices:
            base_light = random.randint(80, 180)
            for i in range(12):
                time_point = now - timedelta(minutes=i * 5)
                variance = random.randint(-40, 40)
                intensity = max(20, min(400, base_light + variance))
                lamp = "on" if intensity < 150 else "off"
                data = LightData(
                    device_id=dev.id,
                    light_intensity=intensity,
                    lamp_status=lamp,
                    voltage=218 + random.random() * 6,
                    reported_at=time_point,
                )
                db.add(data)

        command_types = ["TURN_ON", "TURN_OFF", "SET_BRIGHTNESS"]
        for dev in created_devices[:2]:
            for i in range(2):
                cmd = ControlLog(
                    device_id=dev.id,
                    command=command_types[i % 3],
                    source="manual",
                    result="success",
                    request_payload={"command": command_types[i % 3], "source": "manual"},
                )
                db.add(cmd)

        alarm_device = created_devices[2]
        alarm = AlarmLog(
            device_id=alarm_device.id,
            alarm_type="offline",
            alarm_level="warning",
            alarm_content=f"{alarm_device.device_name} 心跳超时已离线",
            handled=False,
        )
        db.add(alarm)

        db.commit()
        print("[*] 初始化完成!")
        print("[*] 账号: admin / admin123")

except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()


from app.main import app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

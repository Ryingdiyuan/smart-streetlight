"""临时启动脚本：使用 SQLite 和模拟数据，完全不修改原代码"""
import os
import sys
from pathlib import Path

# 优先设置当前目录
backend_dir = Path(__file__).parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

# 关键：先加载数据库模块，然后动态替换它！
from app.core import config, database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 替换为 SQLite 数据库
DB_FILE = backend_dir / "temp_db.sqlite3"
SQLITE_URL = f"sqlite:///{str(DB_FILE).replace(os.sep, '/')}"
print("[*] Using SQLite database:", SQLITE_URL)

database.engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
database.SessionLocal = sessionmaker(
    bind=database.engine, autoflush=False, autocommit=False, future=True
)

# 修改配置以禁用不需要的服务
config.settings.mqtt_enabled = False
config.settings.scheduler_enabled = False


def init_sample_data():
    """初始化模拟数据"""
    from app.core.database import SessionLocal
    from app.core.database import Base
    from app.models.device import Device
    from app.models.threshold_config import ThresholdConfig
    from app.models.light_data import LightData
    from app.models.control_log import ControlLog
    from app.models.alarm_log import AlarmLog
    from app.models.user import User
    from passlib.context import CryptContext
    from datetime import datetime, timedelta
    import random

    db = SessionLocal()
    try:
        # 创建表
        Base.metadata.create_all(bind=database.engine)

        if db.query(Device).count() > 0:
            print("[*] Data exists, skip initialization")
            return

        print("[*] Creating sample data...")

        # 1. 创建管理员用户
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        admin = User(
            username="admin",
            password_hash=pwd_context.hash("admin123"),
            role="admin",
            is_active=True,
        )
        db.add(admin)

        # 2. 创建设备
        devices_info = [
            {"code": "SL-001", "name": "东门入口路灯", "loc": "学校东门入口", "online": True},
            {"code": "SL-002", "name": "图书馆门口", "loc": "图书馆正门", "online": True},
            {"code": "SL-003", "name": "教学楼C栋", "loc": "第三教学楼前", "online": False},
            {"code": "SL-004", "name": "学生宿舍区", "loc": "一号学生公寓", "online": True},
            {"code": "SL-005", "name": "体育场入口", "loc": "主体育场入口", "online": True},
        ]

        created_devices = []
        for d in devices_info:
            device = Device(
                device_code=d["code"],
                device_name=d["name"],
                location=d["loc"],
                status="online" if d["online"] else "offline",
            )
            db.add(device)
            created_devices.append(device)

        db.flush()

        # 3. 为每个设备创建阈值配置
        for dev in created_devices:
            th = ThresholdConfig(
                device_id=dev.id, low_threshold=100, high_threshold=300, enabled=True
            )
            db.add(th)

        # 4. 生成光照历史数据
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

        # 5. 生成控制日志
        command_types = ["TURN_ON", "TURN_OFF", "SET_BRIGHTNESS"]
        for dev in created_devices[:3]:
            for i in range(2):
                cmd = ControlLog(
                    device_id=dev.id,
                    command=command_types[i % 3],
                    source="manual",
                    result="success",
                    request_payload={"command": command_types[i % 3], "source": "manual"},
                )
                db.add(cmd)

        # 6. 生成告警数据
        alarm_device = created_devices[2]  # SL-003 离线设备
        alarm = AlarmLog(
            device_id=alarm_device.id,
            alarm_type="offline",
            alarm_level="warning",
            alarm_content=f"{alarm_device.device_name} 心跳超时已离线",
            handled=False,
        )
        db.add(alarm)

        db.commit()

        print("[+] Sample data created!")
        print(f"    - Generated {len(created_devices)} devices")
        print(f"    - Login: admin / admin123")

    except Exception as e:
        db.rollback()
        print(f"[-] Init failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    init_sample_data()
    print("\n[+] Starting service...")
    uvicorn.run(
        "start_with_mock:app",
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from app.models import (  # noqa: F401
        alarm_log,
        chat_message,
        control_log,
        device,
        light_data,
        sensor,
        threshold_config,
        user,
    )

    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()


def ensure_schema_updates() -> None:
    inspector = inspect(engine)

    if inspector.has_table("devices"):
        device_columns = {column["name"] for column in inspector.get_columns("devices")}
        alter_statements: list[str] = []

        if "sensor_id" not in device_columns:
            alter_statements.append("ADD COLUMN sensor_id INT NULL")
        if "lamp_status" not in device_columns:
            alter_statements.append("ADD COLUMN lamp_status VARCHAR(20) NOT NULL DEFAULT 'OFF'")
        if "control_mode" not in device_columns:
            alter_statements.append("ADD COLUMN control_mode VARCHAR(20) NOT NULL DEFAULT 'manual'")
        if "sensor_control_enabled" not in device_columns:
            alter_statements.append("ADD COLUMN sensor_control_enabled BOOLEAN NOT NULL DEFAULT TRUE")

        if alter_statements:
            with engine.begin() as connection:
                for statement in alter_statements:
                    connection.execute(text(f"ALTER TABLE devices {statement}"))

    if inspector.has_table("sensors"):
        sensor_columns = {column["name"] for column in inspector.get_columns("sensors")}
        alter_statements: list[str] = []

        if "location" not in sensor_columns:
            alter_statements.append("ADD COLUMN location VARCHAR(255) NULL")
        if "latitude" not in sensor_columns:
            alter_statements.append("ADD COLUMN latitude FLOAT NULL")
        if "longitude" not in sensor_columns:
            alter_statements.append("ADD COLUMN longitude FLOAT NULL")
        if "online" not in sensor_columns:
            alter_statements.append("ADD COLUMN online BOOLEAN NOT NULL DEFAULT TRUE")
        if "base_light" not in sensor_columns:
            alter_statements.append("ADD COLUMN base_light INT NOT NULL DEFAULT 120")
        if "variance" not in sensor_columns:
            alter_statements.append("ADD COLUMN variance INT NOT NULL DEFAULT 35")
        if "voltage_base" not in sensor_columns:
            alter_statements.append("ADD COLUMN voltage_base FLOAT NOT NULL DEFAULT 220.5")
        if "telemetry_interval_seconds" not in sensor_columns:
            alter_statements.append("ADD COLUMN telemetry_interval_seconds INT NOT NULL DEFAULT 20")
        if "status_every" not in sensor_columns:
            alter_statements.append("ADD COLUMN status_every INT NOT NULL DEFAULT 1")

        with engine.begin() as connection:
            for statement in alter_statements:
                connection.execute(text(f"ALTER TABLE sensors {statement}"))

            if "sensor_type" in sensor_columns:
                connection.execute(
                    text("ALTER TABLE sensors MODIFY COLUMN sensor_type VARCHAR(50) NOT NULL DEFAULT 'light'")
                )

            # 将历史默认的 5 秒采样间隔平滑迁移为新的 20 秒默认值。
            if "telemetry_interval_seconds" in sensor_columns:
                connection.execute(text("UPDATE sensors SET telemetry_interval_seconds = 20 WHERE telemetry_interval_seconds = 5"))

    if inspector.has_table("alarm_logs"):
        alarm_columns = {column["name"] for column in inspector.get_columns("alarm_logs")}
        alter_statements: list[str] = []

        if "sensor_id" not in alarm_columns:
            alter_statements.append("ADD COLUMN sensor_id INT NULL")

        with engine.begin() as connection:
            for statement in alter_statements:
                connection.execute(text(f"ALTER TABLE alarm_logs {statement}"))

            if "device_id" in alarm_columns:
                connection.execute(text("ALTER TABLE alarm_logs MODIFY COLUMN device_id INT NULL"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

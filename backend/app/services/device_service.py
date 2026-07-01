from sqlalchemy.orm import Session

from app.models.device import Device


def list_devices(db: Session) -> list[Device]:
    return db.query(Device).order_by(Device.id.desc()).all()

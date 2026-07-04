from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import InitAdminRequest


def create_initial_admin(db: Session, admin_create: InitAdminRequest) -> User | None:
    if db.query(User).count() > 0:
        return None

    user = User(
        username=admin_create.username,
        password_hash=hash_password(admin_create.password),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

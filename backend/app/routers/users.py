from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user


def ensure_username_unique(
    db: Session,
    username: str,
    exclude_id: int | None = None,
) -> None:
    query = db.query(User).filter(
        User.username == username,
        User.deleted_at.is_(None),
    )
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)

    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )


def active_admin_count(db: Session, exclude_id: int | None = None) -> int:
    query = db.query(User).filter(User.role == "admin", User.is_active.is_(True))
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.count()


def ensure_not_last_active_admin(db: Session, user: User, update_data: dict) -> None:
    if user.role != "admin" or not user.is_active:
        return

    next_role = update_data.get("role", user.role)
    next_active = update_data.get("is_active", user.is_active)
    if next_role == "admin" and next_active:
        return

    if active_admin_count(db, exclude_id=user.id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用或降级最后一个可用管理员",
        )


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
    search: str | None = Query(None, description="模糊搜索用户名"),
) -> list[User]:
    query = db.query(User).filter(User.deleted_at.is_(None))
    if search:
        query = query.filter(User.username.like(f"%{search}%"))
    return query.order_by(User.id.asc()).all()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> User:
    ensure_username_unique(db, user_create.username)
    user = User(
        username=user_create.username,
        password_hash=hash_password(user_create.password),
        role=user_create.role,
        is_active=user_create.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> User:
    user = get_user_or_404(db, user_id)
    update_data = user_update.model_dump(exclude_unset=True)
    ensure_not_last_active_admin(db, user, update_data)

    if "username" in update_data:
        ensure_username_unique(db, update_data["username"], exclude_id=user_id)
        user.username = update_data["username"]

    if update_data.get("password"):
        user.password_hash = hash_password(update_data["password"])

    if "role" in update_data:
        user.role = update_data["role"]

    if "is_active" in update_data:
        user.is_active = update_data["is_active"]

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> None:
    user = get_user_or_404(db, user_id)

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if user.role == "admin" and user.is_active:
        if active_admin_count(db, exclude_id=user_id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除最后一个可用管理员",
            )

    user.deleted_at = datetime.now(timezone.utc)
    db.commit()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.models.user import User
from app.schemas.auth import InitAdminRequest, LoginRequest, LoginResponse, UserRead
from app.services.auth_service import authenticate_user, create_initial_admin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/init-admin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def init_admin(
    admin_create: InitAdminRequest,
    db: Session = Depends(get_db),
) -> User:
    user = create_initial_admin(db, admin_create)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统已存在用户，不能重复初始化管理员",
        )
    return user


@router.post("/login", response_model=LoginResponse)
def login(
    login_request: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    user = authenticate_user(db, login_request.username, login_request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已禁用",
        )

    return LoginResponse(
        access_token=create_access_token(user),
        user=user,
    )


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

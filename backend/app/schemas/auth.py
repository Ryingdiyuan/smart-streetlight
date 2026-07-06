from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserRole


class InitAdminRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenUser(BaseModel):
    id: int
    username: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: TokenUser

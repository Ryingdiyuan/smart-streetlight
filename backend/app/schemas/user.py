from typing import Literal

from pydantic import BaseModel, ConfigDict

UserRole = Literal["admin", "maintainer", "user"]


class UserBase(BaseModel):
    username: str
    role: UserRole = "user"
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

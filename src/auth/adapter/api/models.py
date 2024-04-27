from __future__ import annotations

import enum
import uuid
from typing import Literal

from pydantic import BaseModel, Field, EmailStr

from auth import domain


class UserKind(str, enum.Enum):
    TRAINEE = "trainee"
    COACH = "coach"


class UserCreate(BaseModel):
    kind: UserKind
    email: EmailStr = Field(examples=["johndoe@example.com"])
    first_name: str = Field(examples=["John", "Иван"])
    last_name: str = Field(examples=["Doe", "Иванов"])
    password: str = Field(examples=["strong_passw0rd"])


class UserGet(BaseModel):
    user_id: uuid.UUID
    kind: UserKind
    email: EmailStr = Field(examples=["johndoe@example.com"])
    first_name: str = Field(examples=["John", "Иван"])
    last_name: str = Field(examples=["Doe", "Иванов"])
    is_active: bool

    @classmethod
    def from_domain(cls, user: domain.User) -> UserGet:
        return cls(
            user_id=user.id,
            kind=user.kind,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )


class UserPatch(BaseModel):
    first_name: str | None = Field(examples=["John", "Иван"])
    last_name: str | None = Field(examples=["Doe", "Иванов"])


class IssuedToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = Field(default="bearer")

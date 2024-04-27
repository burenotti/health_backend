import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Callable

import jwt
import sqlalchemy.exc

from auth.domain import User, UserKind
from pydantic import BaseModel, Field, ConfigDict

from auth.service_layer import UserUnitOfWork


@dataclass(frozen=True)
class TokensPair:
    access_token: str
    refresh_token: str
    token_type: str = field(default="bearer", init=False)


class InvalidCredentials(Exception):
    pass


class AuthorizationExpired(InvalidCredentials):
    pass


class UserAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


def create_user(
    uow: UserUnitOfWork,
    user_id: uuid.UUID,
    kind: UserKind,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> User:
    with uow:
        user = User.new(
            user_id=user_id,
            kind=kind,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        uow.user_repo.add(user)
        try:
            uow.commit()
        except sqlalchemy.exc.IntegrityError:
            raise UserAlreadyExistsError("user with given id or email already exists")
        return user


def get_user_by_id(uow: UserUnitOfWork, user_id: uuid.UUID) -> User | None:
    with uow:
        return uow.user_repo.get(user_id)


class AccessTokenClaims(BaseModel):
    user_id: uuid.UUID = Field(alias="sub")
    issued_at: datetime = Field(alias="iat")
    expires_at: datetime = Field(alias="exp")
    email: str = Field(alias="email")
    first_name: str = Field(alias="first_name")
    last_name: str = Field(alias="last_name")

    model_config = ConfigDict(
        populate_by_name=True,
    )


def issue_access_token(
    user: User,
    secret: str,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ttl: timedelta = timedelta(hours=1),
) -> str:
    now_ = now()
    claims = AccessTokenClaims(
        user_id=user.id,
        issued_at=now_,
        expires_at=now_ + ttl,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    return jwt.encode(claims.model_dump(mode="json"), secret, algorithm="HS256")


class RefreshTokenClaims(BaseModel):
    authorization_id: uuid.UUID = Field(alias="jti")
    user_id: uuid.UUID = Field(alias="sub")
    issued_at: datetime = Field(alias="iat")
    expires_at: datetime = Field(alias="exp")

    model_config = ConfigDict(
        populate_by_name=True,
    )


def issue_refresh_token(
    user_id: uuid.UUID,
    auth_id: uuid.UUID,
    secret: str,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ttl: timedelta = timedelta(days=7),
) -> str:
    now_ = now()
    claims = RefreshTokenClaims(
        authorization_id=auth_id,
        user_id=user_id,
        issued_at=now_,
        expires_at=now_ + ttl,
    )

    return jwt.encode(claims.model_dump(mode="json"), secret, algorithm="HS256")


def decode_refresh_token(
    token: str,
    secret: str,
) -> RefreshTokenClaims:
    return RefreshTokenClaims.model_validate(
        jwt.decode(token, secret, "HS256", verify=False)
    )


def validate_token(token: str, secret: str) -> AccessTokenClaims:
    raw_claims = jwt.decode(token, secret, algorithms=["HS256"], verify=True)
    return AccessTokenClaims.model_validate(raw_claims)


def login(email: str, password: str, uow: UserUnitOfWork, secret: str) -> TokensPair:
    with uow:
        user = uow.user_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentials("User with provided email does not exist")

        if (auth := user.auth(password)) is None:
            raise InvalidCredentials("Invalid credentials")

        uow.user_repo.persist(user)
        uow.commit()

        access_token = issue_access_token(user, secret)
        refresh_token = issue_refresh_token(user.id, auth.authorization_id, secret)

        return TokensPair(access_token, refresh_token)


def refresh(
    refresh_token: str,
    uow: UserUnitOfWork,
    secret: str,
) -> TokensPair:
    with uow:
        now = datetime.now(timezone.utc)
        claims = decode_refresh_token(refresh_token, secret)
        user = uow.user_repo.get_by_authorization(claims.authorization_id)
        if user is None:
            raise InvalidCredentials("Invalid refresh token")

        if user.find_authorization(claims.authorization_id).active_until < now:
            raise AuthorizationExpired(
                f"Authorization {claims.authorization_id} has expired"
            )

        access_token = issue_access_token(user, secret)

        return TokensPair(access_token, refresh_token)

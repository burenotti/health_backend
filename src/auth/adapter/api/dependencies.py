import uuid
import jwt
from fastapi import Depends, Request, HTTPException, status, Query
from typing import Annotated, Literal
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, Session
from auth.service_layer import UserUnitOfWork, auth
from common import AbstractMessageBus
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from health.config import Config


def get_config(request: Request) -> Config:
    return request.app.config


def get_engine(
    request: Request,
) -> Engine:
    return request.app.engine


def get_sessionmaker(
    engine: Annotated[Engine, Depends(get_engine)],
) -> sessionmaker[Session]:
    return sessionmaker(engine, autoflush=False, expire_on_commit=False)


def get_unit_of_work(
    bus: Annotated[AbstractMessageBus, Depends()],
    sessionmaker_: Annotated[sessionmaker[Session], Depends(get_sessionmaker)],
) -> UserUnitOfWork:
    return UserUnitOfWork(bus, sessionmaker_)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/auth/login")


def get_current_user_id(
    token: Annotated[str, Depends(oauth2_scheme)],
    config: Annotated[Config, Depends(get_config)],
) -> uuid.UUID:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = auth.validate_token(token, config.app.secret)
    except jwt.PyJWTError:
        raise credentials_exception

    return claims.user_id


refresh_token_bearer = HTTPBearer()


def get_refresh_token(
    token: Annotated[HTTPAuthorizationCredentials, Depends(refresh_token_bearer)],
    grant_type: Annotated[Literal["refresh_token"], Query(alias="grant_type")],
) -> str:
    assert grant_type == "refresh_token"
    return token.credentials

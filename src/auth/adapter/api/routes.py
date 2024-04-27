import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Body, Depends, Response, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from health.config import Config
from .dependencies import (
    get_unit_of_work,
    get_current_user_id,
    get_config,
    get_refresh_token,
)
from .models import UserCreate, UserGet, UserPatch, IssuedToken
from auth.service_layer import UserUnitOfWork, auth

router = APIRouter(
    prefix="/users",
    tags=["auth"],
)


@router.post(
    "/{user_id}",
    description="Creates user profile",
    status_code=201,
    responses={
        201: {},
        400: {},
        429: {},
    },
)
def create_user(
    user_id: Annotated[uuid.UUID, Path()],
    user_data: Annotated[UserCreate, Body()],
    uow: Annotated[UserUnitOfWork, Depends(get_unit_of_work)],
) -> Response:
    try:
        auth.create_user(
            uow=uow,
            user_id=user_id,
            kind=user_data.kind,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,
            email=user_data.email,
        )
        return Response(status_code=status.HTTP_201_CREATED)
    except auth.UserAlreadyExistsError as e:
        raise HTTPException(
            detail=e.args[0],
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get(
    "/{user_id}",
    summary="Returns user by id",
    response_model=UserGet,
    responses={
        200: {},
        400: {},
        429: {},
    },
)
def get_user_by_id(
    user_id: Annotated[uuid.UUID, Path()],
    uow: Annotated[UserUnitOfWork, Depends(get_unit_of_work)],
) -> UserGet:
    user = auth.get_user_by_id(uow, user_id)
    return UserGet.from_domain(user)


@router.get(
    "/",
    summary="Returns info about current user",
    response_model=UserGet | None,
    responses={
        200: {},
        204: {},
        429: {},
    },
)
def get_current_user(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    uow: Annotated[UserUnitOfWork, Depends(get_unit_of_work)],
) -> UserGet | None:
    user = auth.get_user_by_id(uow, user_id)
    return UserGet.from_domain(user)


@router.patch(
    "/{user_id}",
    summary="Updates user info",
    response_model=UserGet,
    responses={
        200: {},
        400: {},
        429: {},
    },
)
def patch_user_by_id(
    user_id: uuid.UUID = Path(),
    user_info: UserPatch = Body(),
) -> UserGet:
    pass


@router.post(
    "/auth/login",
    summary="Log user in and returns refresh and access token",
    response_model=IssuedToken,
)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    uow: Annotated[UserUnitOfWork, Depends(get_unit_of_work)],
    config: Annotated[Config, Depends(get_config)],
) -> IssuedToken:
    token = auth.login(form.username, form.password, uow, config.app.secret)
    return IssuedToken(
        access_token=token.access_token,
        refresh_token=token.refresh_token,
    )


@router.post(
    "/auth/refresh",
    summary="Returns new access token",
    response_model=IssuedToken,
)
def refresh(
    token: Annotated[str, Depends(get_refresh_token)],
    uow: Annotated[UserUnitOfWork, Depends(get_unit_of_work)],
    config: Annotated[Config, Depends(get_config)],
) -> IssuedToken:
    try:
        tokens = auth.refresh(token, uow, config.app.secret)

        return IssuedToken(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    except auth.AuthorizationExpired as e:
        raise HTTPException(
            detail=e.args[0],
            status_code=status.HTTP_400_BAD_REQUEST,
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

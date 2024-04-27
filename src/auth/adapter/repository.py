from __future__ import annotations

import heapq
import uuid
from typing import Iterable, Iterator, TypeVar

import sqlalchemy as sa
from datetime import datetime

from sqlalchemy.orm import (
    Session,
    mapped_column,
    Mapped,
    relationship,
    joinedload,
    selectinload,
)

from common.domain import DomainEvent
from common.repository import AbstractRepository
from common.sql import Base, TimeMixin
from auth import domain

__all__ = ["UserRepository"]


class UserRepository(AbstractRepository):
    def __init__(self, session: Session) -> None:
        self.session = session
        self.__seen = set[domain.User]()

    def add(self, user: domain.User) -> None:
        self.session.add(self._to_db_model(user))

    def persist(self, user: domain.User) -> None:
        merged = self.session.merge(
            self._to_db_model(user), options=[joinedload(User.authorizations)]
        )
        self.session.add(merged)

    def get(self, user_id: uuid.UUID) -> domain.User | None:
        query = (
            sa.select(User)
            .where(User.user_id == user_id)
            .options(selectinload(User.authorizations))
        )
        return one_or_none(self._find_all(query))

    def get_by_email(self, email: str) -> domain.User | None:
        query = (
            sa.select(User)
            .where(User.email == email)
            .options(selectinload(User.authorizations))
        )
        return one_or_none(self._find_all(query))

    def get_by_authorization(self, auth_id: uuid.UUID) -> domain.User | None:
        query = (
            sa.select(User)
            .where(
                Authorization.logout_at.is_(None)
                & (Authorization.authorization_id == auth_id)
            )
            .options(selectinload(User.authorizations))
        )
        return one_or_none(self._find_all(query))

    def collect_events(self) -> Iterable[DomainEvent]:
        heap = list[DomainEvent]()
        for user in self.__seen:
            while event := user.pop_event():
                heapq.heappush(heap, event)

        return heap

    def _find_all(self, query) -> Iterator[domain.User]:
        with self.session.execute(query) as result:
            for user in result.scalars().all():
                yield self._to_domain(user)

    def _to_domain(self, db_model: User) -> domain.User:
        return domain.User(
            user_id=db_model.user_id,
            email=db_model.email,
            first_name=db_model.first_name,
            last_name=db_model.last_name,
            password_hash=db_model.password_hash,
            salt=db_model.salt,
            is_active=db_model.is_active,
            authorizations=[self._auth_to_domain(t) for t in db_model.authorizations],
            kind=db_model.kind,
        )

    def _to_db_model(self, user: domain.User) -> User:
        return User(
            user_id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            password_hash=user.password_hash,
            salt=user.salt,
            is_active=user.is_active,
            authorizations=[
                self._auth_to_db_model(user.id, t) for t in user.authorizations
            ],
            kind=user.kind,
        )

    def _auth_to_db_model(
        self, user_id: uuid.UUID, auth: domain.Authorization
    ) -> Authorization:
        return Authorization(
            authorization_id=auth.authorization_id,
            logout_at=auth.logout_at,
            active_until=auth.active_until,
            user_id=user_id,
        )

    def _auth_to_domain(self, db_model: Authorization) -> domain.Authorization:
        return domain.Authorization(
            authorization_id=db_model.authorization_id,
            active_until=db_model.active_until,
            logout_at=db_model.logout_at,
        )


class Authorization(Base, TimeMixin):
    __tablename__ = "authorizations"

    authorization_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    active_until: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    logout_at: Mapped[datetime] = mapped_column(nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.user_id"))


class User(Base, TimeMixin):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    kind: Mapped[domain.UserKind] = mapped_column()
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str] = mapped_column()
    salt: Mapped[str] = mapped_column()
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column()
    authorizations: Mapped[list[Authorization]] = relationship(
        "Authorization", lazy="joined", cascade="all, delete-orphan"
    )


T = TypeVar("T")


def one_or_none(iterable: Iterable[T]) -> T | None:
    try:
        return next(iter(iterable))
    except StopIteration:
        return None

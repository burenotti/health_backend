from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from common.domain import Aggregate

from . import events
from .service import hash_password, validate_password

__all__ = ["User", "UserKind", "Authorization"]


class UserKind(str, enum.Enum):
    COACH = "coach"
    TRAINEE = "trainee"


class User(Aggregate[uuid.UUID]):
    TOKEN_TTL = timedelta(days=7)

    def __init__(
        self,
        kind: UserKind,
        user_id: uuid.UUID,
        email: str,
        first_name: str,
        last_name: str,
        is_active: bool,
        password_hash: str,
        salt: str,
        authorizations: list[Authorization],
    ) -> None:
        super().__init__(user_id)
        self.kind = kind
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = password_hash
        self.salt = salt
        self.is_active = is_active
        self.authorizations = authorizations

    @classmethod
    def new(
        cls,
        kind: UserKind,
        user_id: uuid.UUID,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> User:
        password_hash, salt = hash_password(password)

        user = User(
            kind, user_id, email, first_name, last_name, True, password_hash, salt, []
        )
        event = events.UserCreated(cls.now(), user.id, email, kind)
        user.push_event(event)
        return user

    def auth(self, password: str) -> Authorization | None:
        if not validate_password(password, self.password_hash, self.salt):
            return None

        auth = self._issue_token()
        self.authorizations.append(auth)
        return auth

    def logout(self, auth_id: uuid.UUID) -> None:
        auth = self.find_authorization(auth_id)
        if auth.logout_at is None:
            auth.logout_at = self.now()

    def find_authorization(self, auth_id: uuid.UUID) -> Authorization | None:
        try:
            return next(a for a in self.authorizations if a.authorization_id == auth_id)
        except StopIteration:
            return None

    @classmethod
    def _issue_token(cls) -> Authorization:
        return Authorization(
            authorization_id=uuid.uuid4(),
            active_until=cls.now() + cls.TOKEN_TTL,
            logout_at=None,
        )


@dataclass
class Authorization:
    authorization_id: uuid.UUID
    active_until: datetime
    logout_at: datetime | None = None


def authorization_is_active(token: Authorization, now: datetime | None = None) -> bool:
    if now is None:
        now = datetime.now(timezone.utc)

    return token.logout_at is None and token.active_until < now

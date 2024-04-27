import uuid
from dataclasses import dataclass
from typing import Literal

from common.domain import DomainEvent


@dataclass(frozen=True)
class UserCreated(DomainEvent):
    user_id: uuid.UUID
    email: str
    kind: Literal["coach", "trainee"]

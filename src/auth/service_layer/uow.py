from typing import cast

from auth.adapter.repository import UserRepository
from common import SQLUnitOfWork, AbstractMessageBus
from sqlalchemy.orm import sessionmaker, Session


class UserUnitOfWork(SQLUnitOfWork):
    def __init__(self, bus: AbstractMessageBus, sessionmaker_: sessionmaker[Session]):
        super().__init__(bus, sessionmaker_, [UserRepository])

    @property
    def user_repo(self) -> UserRepository:
        return cast(UserRepository, self._repositories[UserRepository])

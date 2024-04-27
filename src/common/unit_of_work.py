import abc
from typing import Callable, Iterable, Self, TypeVar, Type

from sqlalchemy.orm import sessionmaker, Session
from common.repository import AbstractRepository
from common.domain import DomainEvent
from common.service_layer import AbstractMessageBus

TID = TypeVar("TID")


class UnitOfWorkError(Exception):
    pass


class AbstractUnitOfWork(abc.ABC):
    _repositories: dict[Type, AbstractRepository]

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None:
            self.rollback()

    @abc.abstractmethod
    def commit(self) -> None:
        pass

    @abc.abstractmethod
    def rollback(self) -> None:
        pass

    def publish_events(self) -> Iterable[DomainEvent]:
        all_events = list[DomainEvent]()
        for repo in self._repositories.values():
            all_events.extend(repo.collect_events())

        all_events.sort(key=lambda event: event.time)
        return all_events

    @abc.abstractmethod
    def _publish_events(self, new_events: Iterable[DomainEvent]) -> None:
        pass


class SQLUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        bus: AbstractMessageBus,
        sessionmaker_: sessionmaker[Session],
        repo_factories: list[Callable[[Session], AbstractRepository]],
    ) -> None:
        self._bus = bus
        self._storage_factories = repo_factories
        self._repositories = dict[Type, AbstractRepository]()
        self._sessionmaker = sessionmaker_
        self._session: Session | None = None

    def _init_repositories(self) -> None:
        for factory in self._storage_factories:
            repo = factory(self._session)
            self._repositories[type(repo)] = repo

    def _dispose_repositories(self) -> None:
        self._repositories = {}

    def __enter__(self) -> Self:
        if self._session is not None:
            raise UnitOfWorkError(
                "Can't begin new session until previous one is not finished"
            )

        self._session = self._sessionmaker()
        self._session.begin()
        self._init_repositories()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is None:
            raise UnitOfWorkError(
                "Can't finish not started session. Maybe a race condition"
            )

        self.rollback()
        self._dispose_repositories()

        self._session.close()

        result = super().__exit__(exc_type, exc_val, exc_tb)
        self._session = None
        return result

    def commit(self) -> None:
        if self._session is None:
            raise UnitOfWorkError("Can't commit not started session")
        self._session.commit()
        self._bus.publish(*self.publish_events())

    def rollback(self) -> None:
        if self._session is None:
            raise UnitOfWorkError("Can't rollback not started session")
        self._session.rollback()

    def _publish_events(self, new_events: Iterable[DomainEvent]) -> None:
        self._bus.publish(*new_events)

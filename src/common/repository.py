import abc
from typing import TypeVar, Generic, Iterable

from .domain import DomainEvent

T = TypeVar("T")
TID = TypeVar("TID")


class AbstractRepository(abc.ABC, Generic[T, TID]):
    @abc.abstractmethod
    def add(self, item: T) -> None:
        pass

    @abc.abstractmethod
    def persist(self, item: T) -> None:
        pass

    @abc.abstractmethod
    def get(self, item_id: TID) -> T:
        pass

    @abc.abstractmethod
    def collect_events(self) -> Iterable[DomainEvent]:
        pass

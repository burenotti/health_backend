import heapq
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import total_ordering
from typing import Generic, TypeVar


class DomainError(Exception):
    pass


@total_ordering
@dataclass(frozen=True, eq=True)
class DomainEvent:
    at: datetime

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, DomainEvent):
            return False

        return self.at < other.at


ID = TypeVar("ID")


class Aggregate(Generic[ID]):
    def __init__(self, aggregate_id: ID) -> None:
        self.__id = aggregate_id
        self.__pending_events = list[DomainEvent]()

    @property
    def id(self) -> ID:
        return self.__id

    def push_event(self, event: DomainEvent) -> None:
        heapq.heappush(self.__pending_events, event)

    def pop_event(self) -> DomainEvent | None:
        if not self.__pending_events:
            return None
        return heapq.heappop(self.__pending_events)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

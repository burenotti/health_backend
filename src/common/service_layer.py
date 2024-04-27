import abc

from common.domain import DomainEvent


class AbstractMessageBus(abc.ABC):
    def publish(self, *events: DomainEvent):
        pass

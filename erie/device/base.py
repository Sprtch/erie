from abc import ABC, abstractmethod
import dataclasses
import logging


@dataclasses.dataclass
class Device(ABC):
    name: str
    """Familiar name to give to a device."""

    def __post_init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")

    def connect(self):
        # TODO send a message that notificate the disconnection.
        pass

    def disconnect(self):
        # TODO send a message that notificate the disconnection.
        pass

    @abstractmethod
    def read_loop(self, stop_event=None):
        ...

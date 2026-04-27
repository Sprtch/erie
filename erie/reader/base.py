from abc import ABC, abstractmethod
from typing import Optional, Iterator, Any
import dataclasses
import logging
import threading


@dataclasses.dataclass
class Reader(ABC):
    """A `Reader` is a device that forware message events.

    Typically this will be assigned to a 'barcode scanning' device but can
    be generalized to any type of device tthat can read inputs.
    """

    def __post_init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.type}")

    @property
    @abstractmethod
    def type(self): ...

    # def export_config(self) -> str:
    #     """Return a string in JSON format of the configuration specificity of the current reading device.
    #
    #     This function needs to be implemented in the specialized class.
    #     """
    #     raise NotImplementedError

    @abstractmethod
    def present(self) -> bool:
        """Whether or not the reading device is currently available.

        This function needs to be implemented in the specialized class.
        """
        ...

    def connected(self) -> bool:
        """Whether or not the reading device is currently connected.

        By default is the same as `present` method.
        """
        return self.present()

    @abstractmethod
    def read(self) -> str | None:
        """Read content in child class (non blocking).

        This function needs to be implemented in the specialized class.
        """
        ...

    def retrieve(self, stop_event: threading.Event, poll_timeout: float = 1.0) -> Iterator[str]:
        while self.connected():
            # Check stop_event between polls so we exit cleanly even when
            # the device is stopped but no new data has arrived yet.
            if stop_event is not None and stop_event.is_set():
                self.logger.debug("stop_event set: exiting")
                return

            content = self.read()
            if content is None:
                continue

            yield content.rstrip("\n")

    def connect(self):
        self.logger.debug("Connecting")

    def disconnect(self):
        self.logger.debug("Disconnecting")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return self

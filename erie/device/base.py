from abc import ABC, abstractmethod
import dataclasses
import logging


@dataclasses.dataclass
class Device(ABC):
    """Abstract base for single unit of devices ran in thread.

    Provides lifecycle management (connect/disconnect) via context manager
    protocol and logging. Concrete subclasses must implement `read_loop`.
    """

    name: str
    """Familiar name to give to a device."""

    def __post_init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.name}")

    def connect(self):
        """Init function executed on device start."""
        self.logger.info("Connecting")

    def disconnect(self):
        """Clean function executed on device stop."""
        self.logger.info("Disconnecting")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return self

    @abstractmethod
    def read_loop(self, stop_event=None):
        """Read, and communication, loop.

        Must implement the logic to stop the loop based on `stop_event`.
        """
        ...

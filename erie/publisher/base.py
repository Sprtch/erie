from abc import ABC, abstractmethod
import dataclasses
import logging


@dataclasses.dataclass
class Publisher(ABC):
    """Abstract base class for outbound message channels.

    A Publisher sends processed IPC messages to an external system
    (Redis pub/sub, stdout, etc.).
    Each :class:`~erie.device.device.ErieDevice` owns a Publisher that it uses
    to emit the results of barcode processing.

    Subclass contract:
        - Implement :meth:`available`: return whether the medium is ready.
        - Implement :meth:`send`: deliver a message to the medium.

    Concrete implementations:
        - :class:`~erie.publisher.redis.Redis`: publishes to a Redis channel.
        - :class:`~erie.publisher.stdout.Stdout`: prints JSON to stdout.
    """

    def __post_init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    def available(self) -> bool:
        """Check the publishing medium is available to send message."""
        ...

    @abstractmethod
    def send(self, msg):
        """Publish *msg* to the output medium.

        :param msg: An IPC message (typically :class:`~erie.schema.message.IpcCompleteMessage`
            or a subclass). Serialisation strategy is implementation-defined.
        """
        ...

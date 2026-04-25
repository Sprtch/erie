from abc import ABC, abstractmethod
import dataclasses


@dataclasses.dataclass
class Publisher(ABC):
    """Abstraction publish generic data."""

    @abstractmethod
    def send(self, msg):
        """Publish payload content."""
        ...

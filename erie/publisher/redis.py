from erie.publisher.base import Publisher
import dataclasses


@dataclasses.dataclass
class Redis(Publisher):
    """
    """
    host: str
    channel: str

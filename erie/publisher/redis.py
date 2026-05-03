from erie.publisher.base import Publisher
import dataclasses
import redis
import json


@dataclasses.dataclass
class Redis(Publisher):
    """Publisher that sends messages to a Redis pub/sub channel."""

    host: str = "localhost"
    channel: str = "erie"
    port: int = 6379
    db: int = 0

    def __post_init__(self):
        super().__post_init__()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = redis.Redis(
                host=self.host, port=self.port, db=self.db, decode_responses=True
            )
        return self._client

    def available(self):
        """Verify the redis connection is possible."""
        try:
            return self.client.ping()
        except redis.RedisError:
            self._client = None
            return False

    def send(self, msg):
        """Publish a message to the configured Redis channel.

        Args:
            msg: Message object to publish. Can be:
                - Message: Will be serialized to JSON
                - DevicePresentMessage/DeviceNotPresentMessage: Will be serialized to JSON
                - Any object: Will be converted to string
        """
        try:
            if hasattr(msg, "asdict"):
                payload = json.dumps(msg.asdict())
            elif hasattr(msg, "__dict__"):
                payload = json.dumps(msg.__dict__)
            else:
                payload = str(msg)

            self.client.publish(self.channel, payload)
            self.logger.debug(f"Published to {self.channel}: {payload}")
        except redis.RedisError as e:
            self.logger.error(f"Redis publish error: {e}")
            raise

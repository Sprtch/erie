from erie.reader.base import Reader
import redis
import dataclasses

@dataclasses.dataclass
class RedisReader(Reader):
    """
    The `MsgReader` class intercept incoming messages.

    This class is made to abstract the complexity of listening incoming
    print job messages on a specific channel.
    The class is used by :class`victoria.Printer` to give away a simple API to
    receive new message based on python iterators.
    For now only redis channel are supported but this can be extended in the
    future.
    """

    channel: str
    host: str
    port: int
    db: int
    _client: redis.Redis = dataclasses.field(default=None, init=False, repr=False)
    _pubsub: redis.client.PubSub = dataclasses.field(default=None, init=False, repr=False)

    @property
    def client(self):
        if self._client is None:
            self._client = redis.Redis(
                host=self.host, port=self.port, db=self.db, decode_responses=True
            )
            self._pubsub = self._client.pubsub()

        return self._client

    @property
    def type(self):
        return None

    def present(self):
        """Verify the redis connection is possible."""
        try:
            self.client.ping()
        except redis.RedisError:
            self._client = None
            self._pubsub = None
            return False
        return True

    def connect(self):
        """Connect to the redis channel to read message from.

        :param channel: Channel to connect to.
        """
        self._pubsub.subscribe(self.channel)

    def disconnect(self):
        self._pubsub.unsubscribe(self.channel)

    def read(self):
        msg = self._pubsub.get_message()
        if msg and msg.get("type") in ("message", "pmessage"):
            return msg.get("data")
        return None

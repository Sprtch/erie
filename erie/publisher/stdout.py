from erie.publisher.base import Publisher
import json
import logging

logger = logging.getLogger(__name__)


class Stdout(Publisher):
    def send(self, msg):
        logger.debug(
            f"[{self.__class__.__name__}:{msg.device}] Received the following message"
        )
        print(json.dumps(msg.asdict(), indent=2))

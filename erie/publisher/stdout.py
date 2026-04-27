from erie.publisher.base import Publisher
import json


class Stdout(Publisher):
    def available(self):
        return True

    def send(self, msg):
        self.logger.debug("Received the following message")
        print(json.dumps(msg.asdict(), indent=2))

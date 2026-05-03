"""Stdout publisher for barcode scanner messages.

Prints IPC messages as formatted JSON to standard output. Useful for
debugging and development.
"""

from erie.publisher.base import Publisher
import json


class Stdout(Publisher):
    """Publish messages by printing them as JSON to stdout."""

    def available(self):
        """Return True. Stdout is always available."""
        return True

    def send(self, msg):
        """Print the message as indented JSON to stdout."""
        self.logger.debug("Sending the following message")
        print(json.dumps(msg.asdict(), indent=2))

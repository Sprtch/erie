from erie.publisher.base import Publisher
from erie.reader.base import Reader
from erie.processor.base import Processor
from erie.message import DevicePresentMessage, DeviceNotPresentMessage, Message
import dataclasses
import logging
import time

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Device:
    """Device definition built from the configuration.

    An input device is defined by multiple components:

    - Its name
    - The 'reader' or the input source.
    - The 'formatter' or the method that transform an input message into an
      outbound message.
    - The 'outbound' or the medium to push out the message.
    """

    name: str
    """Familiar name to give to a device."""

    reader: Reader
    """The input source."""

    processor = Processor()
    """Processor to transform a raw input into a message"""

    outbound: Publisher
    """The output source."""

    def disconnect():
        # TODO send a message that notificate the disconnection.
        pass

    def read_loop(self):
        while True: # TODO Handle disconnect
            if not self.reader.present():
                yield DeviceNotPresentMessage()
                time.sleep(5)
            else:
                yield DevicePresentMessage()
                for content in self.reader.retrieve():
                    pass
                    # msg = self.formatter.transform(content)
                    # self.outbound.send(msg)

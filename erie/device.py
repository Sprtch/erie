from erie.publisher.base import Publisher
from erie.reader.base import Reader
from erie.processor.base import Processor
from erie.schema.message import IpcDisconnectMessage, IpcIsAliveMessage, IpcIncompleteMessage
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
      'output' message.
    - The 'output' or the medium to push out the message.
    """

    name: str
    """Familiar name to give to a device."""

    reader: Reader
    """The input source."""

    publisher: Publisher
    """The output source."""

    processor: Processor = dataclasses.field(default_factory=Processor)
    """Processor to transform a raw input into a message"""

    def disconnect(self):
        # TODO send a message that notificate the disconnection.
        pass

    def read_loop(self, stop_event=None):
        logger.info(
            f"[{self.__class__.__name__}:{self.name}] Init `read_loop` function."
        )

        while stop_event is None or not stop_event.is_set():
            if not self.reader.present():
                self.publisher.send(
                    IpcDisconnectMessage(
                        device=self.name,
                    )
                )
                logger.debug(
                    f"[{self.__class__.__name__}:{self.name}] Reader '{self.reader.type}' is not present"
                )
                time.sleep(5)
            else:
                self.publisher.send(
                    IpcIsAliveMessage(
                        device=self.name,
                    )
                )
                logger.info(
                    f"[{self.__class__.__name__}:{self.name}] Reader '{self.reader.type}' connecting."
                )
                with self.reader as reader:
                    for content in reader.retrieve(stop_event):
                        pre_msg = IpcIncompleteMessage(
                            device=self.name,
                            content=content,
                        )
                        processed = self.processor.read(pre_msg)
                        self.publisher.send(processed)
                logger.info(
                    f"[{self.__class__.__name__}:{self.name}] Reader '{self.reader.type}' Disconnected."
                )
        self.publisher.send(
            IpcDisconnectMessage(
                device=self.name,
            )
        )

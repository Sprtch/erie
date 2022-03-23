from despinassy.ipc import create_nametuple
from erie.message import DevicePresentMessage, DeviceNotPresentMessage, Message
from despinassy.Scanner import ScannerTypeEnum
import dataclasses
import logging
import time

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class DeviceWrapper:
    """
    """

    name: str
    """Familiar name to give to a device."""

    redis: str
    """Channel to output the message to."""
    # TODO Maybe this should belong to the processor since the role of the device
    # TODO is only reading incoming message and passing them to the processor.

    def get_type(self):
        return self.DEVICE_TYPE

    def debug(self, msg):
        logger.debug("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def info(self, msg):
        logger.info("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def warning(self, msg):
        logger.warning("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def error(self, msg):
        logger.error("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def export_config(self) -> str:
        """Return a string in JSON format of the configuration specificity of the current reading device.

        This function needs to be implemented in the specialized class.
        """
        raise NotImplementedError

    def present(self) -> bool:
        """Whether or not the reading device is currently available.

        This function needs to be implemented in the specialized class.
        """
        raise NotImplementedError

    def retrieve(self):
        """Generator iterating over the incoming flow of message.

        This function needs to be implemented in the specialized class.
        """
        raise NotImplementedError

    def read_loop(self):
        while True: # TODO Handle disconnect
            if not self.present():
                yield DeviceNotPresentMessage()
                time.sleep(5)
            else:
                yield DevicePresentMessage()
                for x in self.retrieve():
                    yield Message(barcode=x,
                                  device=self.name,
                                  redis=self.redis)

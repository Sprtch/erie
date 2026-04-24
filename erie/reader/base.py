from abc import ABC, abstractmethod
from erie.message import DevicePresentMessage, DeviceNotPresentMessage, Message
# from despinassy.Scanner import ScannerTypeEnum
import dataclasses
import logging
import time

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class Reader(ABC):
    """A `Reader` is a device that forware message events.

    Typically this will be assigned to a 'barcode scanning' device but can
    be generalized to any type of device tthat can read inputs.
    """

    name: str
    """Familiar name to give to a device."""

    # TODO Maybe this should belong to the processor since the role of the device
    # TODO is only reading incoming message and passing them to the processor.

    @abstractmethod
    @property
    def type(self):
        raise NotImplementedError

    # def export_config(self) -> str:
    #     """Return a string in JSON format of the configuration specificity of the current reading device.
    #
    #     This function needs to be implemented in the specialized class.
    #     """
    #     raise NotImplementedError

    @abstractmethod
    def present(self) -> bool:
        """Whether or not the reading device is currently available.

        This function needs to be implemented in the specialized class.
        """
        raise NotImplementedError

    @abstractmethod
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

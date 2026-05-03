from abc import ABC, abstractmethod
from erie.schema.type import ScannerModeEnum
from erie.processor.common import InternalRepresentation
from erie.schema.message import (
    IpcCompleteMessage,
    IpcPrintMessage,
    IpcInventoryMessage,
)
import logging
import dataclasses

logger = logging.getLogger(__name__)


class ProcessorMode(ABC):
    """Mode the 'Device' is currently in.

    Concrete subclasses must implement `process`.
    """

    @property
    @abstractmethod
    def type(self):
        """Return current mode."""
        ...

    @abstractmethod
    def process(self, msg: InternalRepresentation) -> IpcCompleteMessage:
        """Process an `IpcIncompleteMessage` into a `IpcCompleteMessage`, ready to be published."""
        ...


def narrow_internal_representation(msg: InternalRepresentation, target) -> dict:
    """Narrow a msg to `target` type dataclass."""
    valid_keys = {f.name for f in dataclasses.fields(target)}

    msg_dict = msg.asdict()
    return {k: v for k, v in msg_dict.items() if k in valid_keys}


class PrintModeProcessor(ProcessorMode):
    """In this mode, the device send print action to receivers of the device.

    Default mode type.
    """

    @property
    def type(self):
        """Return `ScannerModeEnum.PRINTMODE` type."""
        return ScannerModeEnum.PRINTMODE

    def process(self, msg: InternalRepresentation) -> IpcPrintMessage:
        return IpcPrintMessage(
            **narrow_internal_representation(msg, IpcPrintMessage),
            type=self.type,
        )


class InventoryModeProcessor(ProcessorMode):
    """In this mode, the device send inventory action to receivers of the device."""

    @property
    def type(self):
        """Return `ScannerModeEnum.INVENTORYMODE` type."""
        return ScannerModeEnum.INVENTORYMODE

    def process(self, msg: InternalRepresentation) -> IpcInventoryMessage:
        return IpcInventoryMessage(
            **narrow_internal_representation(msg, IpcInventoryMessage),
            type=self.type,
        )

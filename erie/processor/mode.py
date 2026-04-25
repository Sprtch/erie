# from erie.schema.message import Message
from abc import ABC, abstractmethod
from erie.schema.type import ScannerModeEnum
from erie.schema.message import (
    IpcIncompleteMessage,
    IpcCompleteMessage,
    IpcPrintMessage,
    IpcInventoryMessage,
)
import logging
import dataclasses

logger = logging.getLogger(__name__)


class ProcessorMode(ABC):
    # MODE = ScannerModeEnum.UNDEFINED

    @property
    @abstractmethod
    def type(self): ...

    @abstractmethod
    def process(self, msg: IpcIncompleteMessage, **kwargs) -> IpcCompleteMessage: ...


def narrow_internal_representation(msg: InternalRepresentation, target) -> dict:
    valid_keys = {f.name for f in dataclasses.fields(target)}

    msg_dict = msg.asdict()
    return {k: v for k, v in msg_dict.items() if k in valid_keys}


class PrintModeProcessor(ProcessorMode):
    @property
    def type(self):
        return ScannerModeEnum.PRINTMODE

    def process(self, msg: InternalRepresentation, **kwargs) -> IpcPrintMessage:
        # TODO Return IpcPrintMessage
        return IpcPrintMessage(
            **narrow_internal_representation(msg, IpcPrintMessage),
            type=self.type,
        )


class InventoryModeProcessor(ProcessorMode):
    @property
    def type(self):
        return ScannerModeEnum.INVENTORYMODE

    def process(self, msg: InternalRepresentation, **kwargs):
        # TODO Return IpcPrintMessage
        return IpcInventoryMessage(
            **narrow_internal_representation(msg, IpcInventoryMessage),
            type=self.type,
        )

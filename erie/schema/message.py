"""IPC message types for communication between Erie and its consumers.

Defines the dataclasses used for print, inventory, alive, and disconnect
messages sent over Redis pub/sub or other channels.
"""

import dataclasses
from enum import IntEnum


class IpcMessageType(IntEnum):
    UNDEFINED = 0
    IS_ALIVE = 1
    DISCONNECT = 2
    PRINT = 3
    INVENTORY = 4


@dataclasses.dataclass
class BaseIpcMessage:
    device: str
    """Device name that originate the message"""

    origin: str = "erie"
    """Application that originated the message"""

    def asdict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class IpcIncompleteMessage(BaseIpcMessage):
    content: str = ""
    """Content of the message"""


@dataclasses.dataclass
class IpcCompleteMessage(IpcIncompleteMessage):
    type: IpcMessageType = IpcMessageType.UNDEFINED
    """Message type"""


@dataclasses.dataclass
class IpcPrintMessage(IpcCompleteMessage):
    """Message used to perform a print."""

    type: IpcMessageType = IpcMessageType.PRINT
    """Print message type"""

    quantity: str = "1"
    """Number of copy to perform"""


@dataclasses.dataclass
class IpcInventoryMessage(IpcCompleteMessage):
    """Message used for inventory mode."""

    type: IpcMessageType = IpcMessageType.INVENTORY
    """Inventory message type"""

    action: int = 1
    """Inventory action to perform"""

    quantity: str = "1"
    """Number of action to perform"""

    def asdict(self):
        return dataclasses.asdict(self)


@dataclasses.dataclass
class IpcIsAliveMessage(BaseIpcMessage):
    """Share the device presence to recipients."""

    type: IpcMessageType = IpcMessageType.IS_ALIVE
    """Is alive message type"""


@dataclasses.dataclass
class IpcDisconnectMessage(BaseIpcMessage):
    """Share the device is no longer present to recipients."""

    type: IpcMessageType = IpcMessageType.DISCONNECT
    """Disconnect message type"""

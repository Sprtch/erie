from erie.schema.message import IpcIncompleteMessage
from typing import Optional
from abc import ABC, abstractmethod
import dataclasses


@dataclasses.dataclass
class Quantity:
    """
    Class to represent a quantity in a message and help with the construction
    of 'delayed' quantity or creating number with the help of a barcode
    scanner.
    """

    negative: bool = False
    value: Optional[int] = None
    dotted: bool = False
    floating: Optional[int] = None

    def __str__(self):
        value = 1 if self.value is None else self.value
        if self.dotted:
            return f"{'-' if self.negative else ''}{value}.{self.floating}"
        else:
            return f"{'-' if self.negative else ''}{value}"


@dataclasses.dataclass
class InternalRepresentation(IpcIncompleteMessage):
    quantity: Quantity = dataclasses.field(default_factory=Quantity)
    action: Optional[int] = None

    def asdict(self) -> dict:
        return {
            **dataclasses.asdict(self),
            "quantity": str(self.quantity),
            "action": self.action,
        }


@dataclasses.dataclass
class ProcessorDelay(ABC):
    @abstractmethod
    def delay(self, msg: InternalRepresentation) -> InternalRepresentation: ...


class MultiplierProcessor(ProcessorDelay):
    multiplier: int = 1

    def __init__(self, multiplier: int):
        self.multiplier = multiplier

    def delay(self, msg):
        if msg.quantity.dotted:
            if msg.quantity.floating is None:
                msg.quantity.floating = 1
            msg.quantity.floating *= self.multiplier
        else:
            if msg.quantity.value is None:
                msg.quantity.value = 1
            msg.quantity.value *= self.multiplier

        return msg


class DigitProcessor(ProcessorDelay):
    digit: int = 0

    def __init__(self, digit: int):
        self.digit = digit

    def delay(self, msg):
        if msg.quantity.dotted:
            if msg.quantity.floating is None:
                msg.quantity.floating = self.digit
            else:
                msg.quantity.floating = int(f"{msg.quantity.floating}{self.digit}")
        else:
            if msg.quantity.value is None:
                msg.quantity.value = self.digit
            else:
                msg.quantity.value = int(f"{msg.quantity.value}{self.digit}")

        return msg


class DotProcessor(ProcessorDelay):
    def delay(self, msg):
        if msg.quantity.value is None:
            msg.quantity.value = 0
        msg.quantity.dotted = True
        return msg


class NegativeProcessor(ProcessorDelay):
    """
    The `NegativeProcessor` turns the quantity of the current message into a
    negative number.

    :note: Negative numbers are useful in inventory mode as it will remove
        something from the inventory instead of adding it.
    """

    def delay(self, msg):
        msg.quantity.negative = True
        return msg

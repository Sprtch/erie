"""Delay processors that build a quantity before the next real barcode is processed.

Each processor mutates an :class:`~erie.processor.common.InternalRepresentation`
and is chained into :attr:`~erie.processor.base.Processor._process_pipe` via
barcode commands such as ``SPRTCHCMD:DIGIT``, ``SPRTCHCMD:MULTIPLIER``, etc.
"""

import dataclasses
from abc import ABC, abstractmethod

from erie.processor.common import InternalRepresentation


@dataclasses.dataclass
class ProcessorDelay(ABC):
    """Abstract base for delay processors that mutate a quantity on the next message.

    Concrete subclasses must implement :meth:`delay`, which receives an
    :class:`~erie.processor.common.InternalRepresentation`, mutates it, and
    returns the same object.
    """

    @abstractmethod
    def delay(self, msg: InternalRepresentation) -> InternalRepresentation:
        """Apply this processor's effect to *msg* and return it."""
        ...


class MultiplierProcessor(ProcessorDelay):
    """Multiply the accumulated quantity by the given factor.

    Triggered by ``SPRTCHCMD:MULTIPLIER:<N>``.
    """

    multiplier: int = 1

    def __init__(self, multiplier: int):
        self.multiplier = multiplier

    def delay(self, msg):
        """Multiply the current quantity part by :attr:`multiplier`."""
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
    """Append a digit to the integer or decimal part of the quantity.

    Triggered by ``SPRTCHCMD:DIGIT:<N>``.
    """

    digit: int = 0

    def __init__(self, digit: int):
        self.digit = digit

    def delay(self, msg):
        """Append :attr:`digit` to the current quantity part."""
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
    """Switch quantity building to decimal mode.

    Triggered by ``SPRTCHCMD:DOT``.
    """

    def delay(self, msg):
        """Enable decimal mode and default the integer part to 0 if unset."""
        if msg.quantity.value is None:
            msg.quantity.value = 0
        msg.quantity.dotted = True
        return msg


class NegativeProcessor(ProcessorDelay):
    """Mark the quantity as negative.

    Triggered by ``SPRTCHCMD:NEGATIVE``.

    :note: In inventory mode, negative quantities remove items from inventory.
    """

    def delay(self, msg):
        """Set the quantity's negative flag."""
        msg.quantity.negative = True
        return msg

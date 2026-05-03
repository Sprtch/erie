import dataclasses
from erie.schema.message import IpcIncompleteMessage
from typing import Optional


@dataclasses.dataclass
class Quantity:
    """Numeric quantity built incrementally from chained device commands.

    Before a real barcode arrives, the user can chain device commands
    to construct a quantity.

    For example, scanning:
      - ``SPRTCHCMD:DIGIT:1``
      - ``SPRTCHCMD:DOT``
      - ``SPRTCHCMD:DIGIT:5``

    Result in the quantity ``1.5``.

    The ``__str__`` output is what gets sent in the final IPC message
    (e.g. ``"1.5"`` or ``"-3"``).

    Class to represent a quantity in a message and help with the construction
    of 'delayed' quantity or creating number with the help of a barcode
    scanner.
    """

    negative: bool = False
    """Negative sign flag."""

    value: Optional[int] = None
    """Integer part of the quantity."""

    dotted: bool = False
    """Indication the subsequent digits are decimal."""

    floating: Optional[int] = None
    """Decimal part of the quantity."""

    def __str__(self):
        value = 1 if self.value is None else self.value
        if self.dotted:
            return f"{'-' if self.negative else ''}{value}.{self.floating}"
        else:
            return f"{'-' if self.negative else ''}{value}"


@dataclasses.dataclass
class InternalRepresentation(IpcIncompleteMessage):
    """Intermediate message flowing through the processor delay pipeline.

    When a real barcode arrives, :class:`~erie.processor.base.Processor`
    creates an ``InternalRepresentation`` from the incoming
    :class:`~erie.schema.message.IpcIncompleteMessage`.

    The processor's ``_process_pipe`` (built from chained ``ProcessorDelay`` commands) is
    then applied to this object, mutating its ``quantity`` field.
    """

    quantity: Quantity = dataclasses.field(default_factory=Quantity)
    """Accumulated numeric quantity from chained device commands."""

    action: Optional[int] = None
    """Optional action code (used in inventory to distinguish add/remove operations."""

    def asdict(self) -> dict:
        return {
            **dataclasses.asdict(self),
            "quantity": str(self.quantity),
            "action": self.action,
        }

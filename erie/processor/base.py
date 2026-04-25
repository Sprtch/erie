"""
Processor module for Erie barcode scanner daemon.

Handles message processing, mode management, and command parsing
for barcode scanners and terminal input.
"""

import dataclasses
import logging

from erie.processor.delay import (
    DigitProcessor,
    DotProcessor,
    InternalRepresentation,
    MultiplierProcessor,
    NegativeProcessor,
    ProcessorDelay,
)
from erie.processor.mode import InventoryModeProcessor, PrintModeProcessor, ProcessorMode
from erie.schema.message import (
    IpcCompleteMessage,
    IpcIncompleteMessage,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Processor:
    """
    The `Processor` class act as a super class to handle messages from reading devices.

    This class is used as a super-class of a specialized
    :class`erie.devices.device.DeviceWrapper` to store its current state. The processor
    serve to interpret the incoming stream of string read by a physical or virtual device.
    The attached device can read barcode as well as operation that can be interpreted to modify
    the operating mode of the reading device like:
        - Changing the mode between 'printing' or 'inventory' mode
        - Applying multiplier to lunch multiple print jobs
    """

    _mode: ProcessorMode = dataclasses.field(default_factory=PrintModeProcessor)
    """Internal current mode of execution of the attached reading device (scanner, ...)"""

    _process_pipe: callable = dataclasses.field(default_factory=lambda: lambda x: x)
    """Internal pipe to delay operations on the next normal message"""

    _message: IpcCompleteMessage = None
    """Current processed message"""

    def _reset(self):
        """Reset the processor state completely."""
        self._mode = PrintModeProcessor()
        self._reset_process_pipe()

    def _reset_process_pipe(self):
        """Reset the pipe of delayed function to not apply anything on the next normal message."""
        self._process_pipe = lambda x: x

    def action(self, fun):
        """Direct action that will be called directly as they are scanned."""
        fun()
        self._reset_process_pipe()

    def delay(self, proc: ProcessorDelay):
        """
        Add a new function to the `_process_pipe`.

        This function and all the previous function of the pipe will be used
        when a normal message is read by the attached device.

        :arg proc: Object containing a `delay` method that contain the action
            that need to be applied to the next message.

        :ref :class`erie.processor.delay.ProcessorDelay`
        """
        pipe = self._process_pipe
        self._process_pipe = lambda x: proc.delay(pipe(x))

    def store(self, proc: ProcessorMode):
        """
        Change the current mode of the processor for the attached device.

        :note: Changing a mode will reset the process pipe.
        :ref :class`erie.processor.delay.ProcessorMode`
        """
        self._mode = proc
        self._reset_process_pipe()

    def _process_dispatch(self, msg):
        return self._mode.process(msg)

    def process(self, msg: IpcIncompleteMessage):
        """
        Process a message (not a function message) and apply the process pipe to it.

        The message is then passed to the current mode. Depending on the mode
        the message will have a different behaviour.

        :arg msg: Message coming from an attached device.
        """
        internal_msg = InternalRepresentation(**msg.asdict())
        final_msg = self._process_pipe(internal_msg)
        result = self._process_dispatch(final_msg)
        self._reset_process_pipe()
        return result

    def match(self, content: str):
        """Match message content to operation.

        Parse the content of a message read by an attached device to match it
        with the code it needs to execute.

        :arg content: Message content coming from an attached device.
        """
        if content.startswith("SPRTCHCMD:") and len(content.split(":")) == 3:
            _, processor, argument = content.split(":")
            if processor == "CLEAR":
                return self._reset_process_pipe
            elif processor == "MULTIPLIER":
                number = int(argument) if argument.isdecimal() else 1
                return MultiplierProcessor(number)
            elif processor == "DIGIT":
                number = abs(int(argument)) if argument.isdecimal() else 1
                return DigitProcessor(number)
            elif processor == "DOTTED":
                return DotProcessor()
            elif processor == "NEGATIVE":
                return NegativeProcessor()
            elif processor == "MODE":
                if argument == "INVENTORY":
                    return InventoryModeProcessor()
                elif argument == "PRINT":
                    return PrintModeProcessor()
        else:
            return None

    def read(self, msg: IpcIncompleteMessage) -> IpcCompleteMessage | None:
        """Busy loop reading forever on the incoming messages of the attached device.

        Run a loop intercepting the incoming messages of the attached device to this processor
        and process them to execute the right operation depending on the message content.

        :note This function is blocking and must be run inside a thread.
        """
        mode = self.match(msg.content)
        if isinstance(mode, ProcessorDelay):
            self.delay(mode)
        elif isinstance(mode, ProcessorMode):
            self.store(mode)
        elif callable(mode):
            self.action(mode)
        else:
            return self.process(msg)
        return None

from erie.processor.mode import ProcessorMode, PrintModeProcessor, InventoryModeProcessor
from erie.processor.delay import ProcessorDelay, MultiplierProcessor, NegativeProcessor, DigitProcessor, DotProcessor
from erie.message import Message, DevicePresentMessage, DeviceNotPresentMessage
from despinassy import db
from despinassy import Scanner as ScannerTable


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
    def __init__(self, dev, mode=PrintModeProcessor()):
        self.dev = dev
        """Attached reading device to this processor"""

        self._mode = mode
        """Internal current mode of execution of the attached reading device (scanner, ...)"""

        self._process_pipe = None
        """Internal pipe to delay the execution of operation on the next normal message (not an operation)"""

        self._entry = None
        """Internal reference to a database object representing the attached device to ease its access"""

        self._reset_process_pipe()


    def save_scanner(self):
        """
        Save the attached reading device (scanner) to the database so it's available for the
        other programs using the database.

        :ref :class`despinassy.Scanner`
        """
        q = ScannerTable.query.filter(ScannerTable.name == self.dev.name)
        if q.count():
            self._entry = q.first()
        else:
            self._entry = ScannerTable(name=self.dev.name,
                                       type=self.dev.get_type(),
                                       redis=self.dev.redis,
                                       settings=self.dev.export_config())
            db.session.add(self._entry)
            db.session.commit()

    def _reset_process_pipe(self):
        """
        Reset the pipe of delayed function to not apply anything on the next normal message.
        """
        self._process_pipe = lambda x: x

    def action(self, fun):
        """
        Direct action that will be called directly as they are scanned.
        """
        fun()
        self._reset_process_pipe()

    def delay(self, proc: ProcessorDelay):
        """
        Add a new function to the `_process_pipe`. This function and all the previous function
        of the pipe will be used when a normal message is read by the attached device.

        :arg proc: Object containing a `delay` method that contain the action that need to be applied
            to the next message.

        :ref :class`erie.processor.delay.ProcessorDelay`
        """
        pipe = self._process_pipe
        self._process_pipe = lambda x: proc.delay(pipe(x))

    def store(self, proc: ProcessorMode):
        """
        Function to change the current mode of the processor for the attached device and log it
        to the database.

        :note: Changing  a mode will reset the process pipe.
        :ref :class`erie.processor.delay.ProcessorMode`
        """
        self._mode = proc
        self._entry.mode = proc.MODE
        db.session.commit()
        self._reset_process_pipe()

    def _process_dispatch(self, msg: Message):
        self._mode.process(msg)

    def process(self, msg: Message):
        """
        Process a message (not a function message) and apply the process pipe
        to it and the pass it to the current mode.
        Depending on the mode the message will have a different behaviour.

        :arg msg: Message coming from an attached device.
        """
        final_msg = self._process_pipe(msg)
        self._process_dispatch(final_msg)
        x = self._entry.add_transaction(mode=int(self._mode.MODE),
                                        quantity=int(final_msg.number),
                                        value=final_msg.barcode)
        db.session.add(x)
        db.session.commit()
        self._reset_process_pipe()

    def match(self, msg: Message):
        """
        Parse the content of a message read by an attached device to match it
        with the code it needs to execute.

        :arg msg: Message coming from an attached device.
        """
        if msg.barcode.startswith("SPRTCHCMD:") and len(
                msg.barcode.split(":")) == 3:
            _, processor, argument = msg.barcode.split(":")
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
            return msg

    def read(self):
        """Busy loop reading forever on the incoming messages of the attached device.

        Run a loop intercepting the incoming messages of the attached device to this processor
        and process them to execute the right operation depending on the message content.

        :note This function is blocking and must be run inside a thread.
        """
        self.save_scanner()

        for msg in self.dev.read_loop():
            if isinstance(msg, Message):
                mode = self.match(msg)
                if isinstance(mode, ProcessorDelay):
                    self.delay(mode)
                elif isinstance(mode, ProcessorMode):
                    self.store(mode)
                elif callable(mode):
                    self.action(mode)
                else:
                    self.process(mode)
            elif isinstance(msg, DeviceNotPresentMessage):
                self._entry.available = False
                db.session.commit()
            elif isinstance(msg, DevicePresentMessage):
                self._entry.available = True
                db.session.commit()

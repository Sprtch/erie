from erie.processor.mode import ProcessorMode, PrintModeProcessor, InventoryModeProcessor
from erie.processor.delay import ProcessorDelay, MultiplierProcessor, NegativeProcessor, DigitProcessor, DotProcessor
from erie.message import Message, DevicePresentMessage, DeviceNotPresentMessage
from despinassy import db
from despinassy import Scanner as ScannerTable


class Processor:
    def __init__(self, dev, mode=PrintModeProcessor()):
        self.dev = dev
        self._mode = mode
        self._process_pipe = None
        self._reset_process_pipe()
        self._entry = None

    def save_scanner(self):
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
        self._process_pipe = lambda x: x

    def action(self, fun):
        fun()
        self._reset_process_pipe()

    def delay(self, proc: ProcessorDelay):
        pipe = self._process_pipe
        self._process_pipe = lambda x: proc.delay(pipe(x))

    def store(self, proc: ProcessorMode):
        self._mode = proc
        self._entry.mode = proc.MODE
        db.session.commit()
        self._reset_process_pipe()

    def _process_dispatch(self, msg: Message):
        self._mode.process(msg)

    def process(self, msg: Message):
        final_msg = self._process_pipe(msg)
        self._process_dispatch(final_msg)
        x = self._entry.add_transaction(mode=int(self._mode.MODE),
                                        quantity=int(final_msg.number),
                                        value=final_msg.barcode)
        db.session.add(x)
        db.session.commit()
        self._reset_process_pipe()

    def match(self, msg: Message):
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

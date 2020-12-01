from despinassy import Part, Inventory, db
from despinassy.ipc import create_nametuple
from erie.message import Message
from erie.logger import logger

class ProcessorMode:
    @staticmethod
    def process(msg: Message) -> Message:
        raise NotImplementedError

class PrintModeProcessor(ProcessorMode):
    @staticmethod
    def process(msg: Message) -> Message:
        in_db = Part.query.filter(Part.barcode == msg.barcode).first()
        if in_db:
            msg = create_nametuple(Message, msg._asdict(), name=in_db.name)
            logger.info("[%s] Scanned '%s' and found '%s'" % (msg.origin, msg.barcode, msg.name))
        else:
            msg = create_nametuple(Message, msg._asdict(), name='')
            logger.info("[%s] Scanned '%s'" % (msg.origin, msg.barcode))
        return msg

class InventoryModeProcessor(ProcessorMode):
    @staticmethod
    def process(msg: Message) -> Message:
        return msg

class ProcessorDelay:
    def delay(self, msg: Message) -> Message:
        raise NotImplementedError

class MultiplierProcessor(ProcessorDelay):
    def __init__(self, multiplier):
        self.multiplier = multiplier

    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message, msg, number=(int(msg.number) * self.multiplier))

class Processor:
    def __init__(self, dev):
        self.dev = dev
        self._mode = PrintModeProcessor
        self._process_pipe = None
        self._reset_process_pipe()

    def _reset_process_pipe(self):
        self._process_pipe = lambda x: x

    def delay(self, proc: ProcessorDelay):
        pipe = self._process_pipe
        self._process_pipe = lambda x : proc.delay(pipe(x))

    def store(self, proc: ProcessorMode):
        self._mode = proc

    def process(self, msg):
        result = self._process_pipe(self._mode.process(msg))
        self._reset_process_pipe()
        return result

    def match(self, msg: Message):
        if msg.barcode.startswith("SPRTCHCMD:"):
            _, processor, argument = msg.barcode.split(":")
            if processor == "CANCEL":
                return ("ACTION", self._reset_process_pipe)
            elif processor == "MULTIPLIER":
                number = int(argument) if argument.isdecimal() else 1
                return ("DELAY", MultiplierProcessor(number))
            elif processor == "MODE":
                if argument == "INVENTORY":
                    return ("STORE", InventoryModeProcessor)
                elif argument == "PRINT":
                    return ("STORE", PrintModeProcessor)
        else:
            return ("PROCESS", msg)

        return ("NULL", None)

    def read(self):
        for msg in self.dev.read_loop():
            print(msg)
            mode, arg = self.match(msg)
            if mode == "ACTION":
                arg()
            elif mode == "DELAY":
                self.delay(arg)
            elif mode == "STORE":
                self.store(arg)
            elif mode == "PROCESS":
                yield self.process(arg)

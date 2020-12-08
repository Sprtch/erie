from erie.processor.mode import ProcessorMode, PrintModeProcessor, InventoryModeProcessor
from erie.processor.delay import ProcessorDelay, MultiplierProcessor, NegativeProcessor
from erie.message import Message

class Processor:
    def __init__(self, dev, mode=PrintModeProcessor):
        self.dev = dev
        self._mode = mode
        self._process_pipe = None
        self._reset_process_pipe()

    def _reset_process_pipe(self):
        self._process_pipe = lambda x: x

    def action(self, fun):
        fun()
        self._reset_process_pipe()

    def delay(self, proc: ProcessorDelay):
        pipe = self._process_pipe
        self._process_pipe = lambda x : proc.delay(pipe(x))

    def store(self, proc: ProcessorMode):
        self._mode = proc
        self._reset_process_pipe()

    def process(self, msg):
        result = self._mode.process(self._process_pipe(msg))
        self._reset_process_pipe()
        return result

    def match(self, msg: Message):
        if msg.barcode.startswith("SPRTCHCMD:"):
            _, processor, argument = msg.barcode.split(":")
            if processor == "CLEAR":
                return ("ACTION", self._reset_process_pipe)
            elif processor == "MULTIPLIER":
                number = int(argument) if argument.isdecimal() else 1
                return ("DELAY", MultiplierProcessor(number))
            elif processor == "NEGATIVE":
                return ("DELAY", NegativeProcessor())
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
                self.action(arg)
            elif mode == "DELAY":
                self.delay(arg)
            elif mode == "STORE":
                self.store(arg)
            elif mode == "PROCESS":
                yield self.process(arg)

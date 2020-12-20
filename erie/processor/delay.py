from despinassy.ipc import create_nametuple
from erie.message import Message


class ProcessorDelay:
    def delay(self, msg: Message) -> Message:
        raise NotImplementedError


class MultiplierProcessor(ProcessorDelay):
    def __init__(self, multiplier):
        self.multiplier = multiplier

    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message,
                                msg,
                                number=(msg.number * self.multiplier))


class DigitProcessor(ProcessorDelay):
    def __init__(self, digit):
        self.digit = digit

    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message,
                                msg,
                                number=(msg.number.digit(self.digit)))


class DotProcessor(ProcessorDelay):
    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message, msg, number=(msg.number.dot()))


class NegativeProcessor(ProcessorDelay):
    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message, msg, number=(msg.number * -1))

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
                                number=(int(msg.number) * self.multiplier))


class NegativeProcessor(ProcessorDelay):
    def __init__(self, arg=None):
        pass

    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message, msg, number=(int(msg.number) * -1))

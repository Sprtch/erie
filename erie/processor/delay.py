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
    """
    The `DigitProcessor` enter manually a digit to create a number from it.
    """
    def __init__(self, digit):
        self.digit = digit

    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message,
                                msg,
                                number=(msg.number.digit(self.digit)))


class DotProcessor(ProcessorDelay):
    """
    The `DotProcessor` turns the quantity of the current message into a
    floating number. This processor must be used in conjunction of the
    `DigitProcessor` functions to create a particular floating number.

    :note: Floating numbers are useful in inventory mode
    """
    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message, msg, number=(msg.number.dot()))


class NegativeProcessor(ProcessorDelay):
    """
    The `NegativeProcessor` turns the quantity of the current message into a
    negative number.

    :note: Negative numbers are useful in inventory mode as it will remove
        something from the inventory instead of adding it.
    """
    def delay(self, msg: Message) -> Message:
        return create_nametuple(Message, msg, number=(msg.number * -1))

import dataclasses
from typing import Optional


class DevicePresentMessage:
    pass


class DeviceNotPresentMessage:
    pass


class Quantity:
    """
    Class to represent a quantity in a message and help with the construction
    of 'delayed' quantity or creating number with the help of a barcode
    scanner.
    """
    def __init__(self, value=1.0, default=True, dotted=False, floating=None):
        self.value: float = float(value)
        self.default: bool = default
        self.dotted: bool = dotted
        self.floating: int = floating

    def digit(self, num: int):
        if self.default:
            return Quantity(num, default=False, dotted=False)
        elif self.dotted:
            if self.floating is None:
                newval = float(str(int(self.value)) + "." + str(num))
                return Quantity(newval,
                                default=False,
                                dotted=True,
                                floating=num)

            else:
                newval = float(
                    str(int(self.value)) + "." + str(self.floating) + str(num))
                return Quantity(newval,
                                default=False,
                                dotted=True,
                                floating=int(str(self.floating) + str(num)))
        else:
            return Quantity(float(str(int(self.value)) + str(num)),
                            default=False,
                            dotted=self.dotted)

    def dot(self):
        if self.default:
            return Quantity(0, default=False, dotted=True)
        else:
            return Quantity(int(self), default=False, dotted=True)

    def __add__(self, other):
        other = float(other.value)
        return self.value + other

    def __sub__(self, other):
        other = float(other.value)
        return self.value - other

    def __mul__(self, other):
        other = float(other)
        result = self.value * other
        if int(str(result).split(".")[-1]):
            dotted = True
            floating = int(str(result).split('.')[-1])
        else:
            dotted = False
            floating = None

        return Quantity(result,
                        default=False,
                        dotted=dotted,
                        floating=floating)

    def __div__(self, other):
        other = float(other.value)
        return self.value / other

    def __eq__(self, other):
        if isinstance(other, Quantity):
            return self.value == other.value
        else:
            return other == self.value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __repr__(self):
        return str(self.value)

    def __str__(self):
        return str(self.value)


@dataclasses.dataclass
class Message:
    """
    The content of a message read from a device.
    This class abstract and help to maintain data integrety of the content
    shared between a device and its processor.

    :note: This message only abstract what it shared inside this program and do
        not represent the actual form of what is sent through the other program
        through redis.
    """
    barcode: str
    redis: str
    device: Optional[str] = None
    number: Quantity = Quantity(1)

    def __post_init__(self):
        if isinstance(self.number, int) or isinstance(self.number, float):
            self.number = Quantity(self.number)
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if hasattr(field.type, "__args__") and len(
                    field.type.__args__
            ) == 2 and field.type.__args__[-1] is type(None):
                if value is not None and not isinstance(
                        value, field.type.__args__[0]):
                    raise ValueError(
                        f'Expected {field.name} to be either {field.type.__args__[0]} or None'
                    )
            elif not isinstance(value, field.type):
                raise ValueError(f'Expected {field.name} to be {field.type}, '
                                 f'got {repr(value)}')

    def _asdict(self):
        return dataclasses.asdict(self)

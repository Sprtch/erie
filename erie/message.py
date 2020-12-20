import dataclasses
from typing import Optional


class Quantity(int):
    def __new__(self, value=1):
        return super(Quantity, self).__new__(self, value)

    def __str__(self):
        return "%d" % int(self)

    def __repr__(self):
        return "%d" % int(self)


@dataclasses.dataclass
class Message:
    barcode: str
    device: str
    redis: str
    name: Optional[str] = None
    number: Quantity = Quantity(1)

    def __post_init__(self):
        if isinstance(self.number, int):
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

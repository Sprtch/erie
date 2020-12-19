import dataclasses
from typing import Optional


@dataclasses.dataclass
class Message:
    barcode: str
    device: str
    redis: str
    name: Optional[str] = None
    number: int = 1

    def __post_init__(self):
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if hasattr(field.type, "__args__") and len(
                    field.type.__args__) == 2 and isinstance(
                        field.type.__args__[-1], None):
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

from abc import ABC

import dataclasses

@dataclasses.dataclass
class Publisher(ABC):
    def send(self):
        pass

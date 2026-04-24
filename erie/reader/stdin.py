from erie.reader.base import Reader
from despinassy.Scanner import ScannerTypeEnum
import logging
import dataclasses

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Stdin(Reader):
    # def export_config(self):
    #     return json.dumps({})

    @property
    def type(self):
        return ScannerTypeEnum.STDIN

    def present(self):
        return True

    def retrieve(self):
        while 1:
            line = input()
            if line:
                yield line.upper()

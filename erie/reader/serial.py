from erie.reader.base import Reader
from despinassy.Scanner import ScannerTypeEnum
from typing import Optional
import logging
import dataclasses
import serial
import os

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Serial(Reader):
    """
    """
    path: Optional[str] = None
    deviceid: Optional[str] = None

    def __post_init__(self):
        if not (self.path or self.deviceid):
            logger.error("Must specify a path or device id")

        if self.deviceid:
            self.path = "/dev/serial/by-id/%s" % (self.deviceid)

        self._dev = None

    @property
    def type(self):
        return ScannerTypeEnum.SERIAL

    # def export_config(self):
    #     return json.dumps({
    #         "path": self.path,
    #     })

    def present(self):
        if os.path.exists(self.path):
            logger.info("Barcode scanner found")
            self._dev = serial.Serial(self.path, 9600, timeout=1)
        else:
            logger.debug("Still no barcode scanner found")
            self._dev = None

        return self._dev is not None

    def retrieve(self):
        try:
            while 1:
                line = self._dev.readline().decode('utf-8').strip()
                if line:
                    yield line
        except serial.serialutil.SerialException as e:
            logger.error(e)

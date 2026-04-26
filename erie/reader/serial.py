import dataclasses
import logging
import os
from typing import Optional

import serial

from erie.reader.file import FileStreamReader
from erie.schema.type import ScannerTypeEnum

logger = logging.getLogger(__name__)


class SerialWrapper:
    def __init__(self, dev):
        self._dev = dev

    @property
    def closed(self):
        return not self._dev.is_open

    def readline(self):
        line = self._dev.readline()
        if line:
            return line.decode("utf-8").strip()
        return ""

    def fileno(self):
        return self._dev.fileno()

    def close(self):
        self._dev.close()


@dataclasses.dataclass
class SerialReader(FileStreamReader):
    """Reader device reading from 'serial' linux device."""

    path: str = None
    device_id: Optional[str] = None
    io: Optional = None

    def __post_init__(self):
        if not (self.path or self.device_id):
            logger.error("Must specify a path or device id")

        if self.device_id:
            self.path = f"/dev/serial/by-id/{self.device_id}"

    @property
    def type(self):
        return ScannerTypeEnum.SERIAL

    def connect(self):
        logger.debug(f"[{self.__class__.__name__}] Opening '{self.path}'")
        if os.path.exists(self.path):
            dev = serial.Serial(self.path, 9600, timeout=1)
            self.io = SerialWrapper(dev)

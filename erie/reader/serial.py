"""Serial port reader for barcode scanners.

Wraps pyserial to read barcode data from USB-serial devices.
"""

import dataclasses
import os
import serial
from typing import Optional
from erie.reader.file import FileStreamReader
from erie.schema.type import ScannerTypeEnum


class SerialWrapper:
    """Thin wrapper around a serial.Serial providing an IOBase-like interface."""

    def __init__(self, dev):
        self._dev = dev

    @property
    def closed(self):
        """Return True if the serial port is closed."""
        return not self._dev.is_open

    def readline(self):
        """Read a single line from the serial port, decoding to UTF-8."""
        line = self._dev.readline()
        if line:
            return line.decode("utf-8").strip()
        return ""

    def fileno(self):
        """Return the file descriptor of the serial port."""
        return self._dev.fileno()

    def close(self):
        """Close the serial port."""
        self._dev.close()


@dataclasses.dataclass
class SerialReader(FileStreamReader):
    """Reader device reading from 'serial' linux device.

    Connects to a USB-serial barcode scanner via pyserial at 9600 baud.
    Accepts either a direct device path or a by-id identifier.
    """

    path: str = None
    device_id: Optional[str] = None
    io: Optional = None

    def __post_init__(self):
        super().__post_init__()
        if not (self.path or self.device_id):
            self.logger.error("Must specify a path or device id")

        if self.device_id:
            self.path = f"/dev/serial/by-id/{self.device_id}"

    @property
    def type(self):
        return ScannerTypeEnum.SERIAL

    def connect(self):
        """Open the serial port and wrap it in a SerialWrapper."""
        self.logger.debug(f"[{self.__class__.__name__}] Opening '{self.path}'")
        if os.path.exists(self.path):
            dev = serial.Serial(self.path, 9600, timeout=1)
            self.io = SerialWrapper(dev)

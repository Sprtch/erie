from erie.devices.device import DeviceWrapper
from despinassy.Scanner import ScannerTypeEnum
from typing import Optional
import json
import dataclasses
import serial
import os


@dataclasses.dataclass
class SerialWrapper(DeviceWrapper):
    DEVICE_TYPE: ScannerTypeEnum = ScannerTypeEnum.SERIAL
    path: Optional[str] = None
    deviceid: Optional[str] = None

    def __post_init__(self):
        if not (self.path or self.deviceid):
            self.error("Must specify a path or device id")

        if self.deviceid:
            self.path = "/dev/serial/by-id/%s" % (self.deviceid)

        self._dev = None

    def export_config(self):
        return json.dumps({
            "path": self.path,
        })

    def present(self):
        if os.path.exists(self.path):
            self.info("Barcode scanner found")
            self._dev = serial.Serial(self.path, 9600, timeout=1)
        else:
            self.debug("Still no barcode scanner found")
            self._dev = None

        return self._dev is not None

    def retrieve(self):
        try:
            while 1:
                line = self._dev.readline().decode('utf-8').strip()
                if line:
                    yield line
        except serial.serialutil.SerialException as e:
            self.error(e)

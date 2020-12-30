from erie.devices.device import DeviceWrapper
from despinassy.Scanner import ScannerTypeEnum
import json
import dataclasses


@dataclasses.dataclass
class StdinWrapper(DeviceWrapper):
    DEVICE_TYPE: ScannerTypeEnum = ScannerTypeEnum.STDIN

    def export_config(self):
        return json.dumps({})

    def present(self):
        return True

    def retrieve(self):
        while 1:
            line = input()
            if line:
                yield line

from erie.devices.device import DeviceWrapper
from despinassy.Scanner import ScannerTypeEnum
from evdev import InputDevice, categorize
from evdev.ecodes import EV_KEY, KEY
from typing import Optional
import json
import dataclasses
import os


@dataclasses.dataclass
class InputDeviceWrapper(DeviceWrapper):
    DEVICE_TYPE: ScannerTypeEnum = ScannerTypeEnum.EVDEV
    path: Optional[str] = None
    deviceid: Optional[str] = None

    # Make the keyboard mapping between the scandata received from evdev and
    # the actual value on the keyboard (should be qwerty).
    KEYBOARD_TRANSLATE = {
        # Keyboard code: actual number
        'LEFTSHIFT': '',
        'SEMICOLON': ':',
        'SLASH': '/',
    }

    def __post_init__(self):
        if not (self.path or self.deviceid):
            self.error("Must specify a path or device id")

        if self.deviceid:
            self.path = "/dev/input/by-id/%s" % (self.deviceid)

        self._dev = None

    def export_config(self):
        return json.dumps({
            "path": self.path,
        })

    def present(self):
        if os.path.exists(self.path):
            self.info("Barcode scanner found")
            self._dev = InputDevice(self.path)
            self._dev.grab()
        elif self._dev:
            self._dev.ungrab()  # Test this case
            self._dev = None
            self.warning("Barcode disconnected")
        else:
            self.debug("Still no barcode scanner plugged")

        return self._dev is not None

    def retrieve(self):
        barcode = ''
        try:
            for ev in self._dev.read_loop():
                if ev.type == EV_KEY:
                    data = categorize(ev)
                    if (data.keystate == 0):
                        # Remove the "KEY_" default character of ecode to only get the key
                        key = KEY[data.scancode][4:]
                        key = InputDeviceWrapper.KEYBOARD_TRANSLATE.get(
                            key, key)
                        if (key is None and barcode) or key == 'ENTER':
                            yield barcode
                            barcode = ''
                        elif len(key):
                            barcode += str(key)
        except OSError:
            self.warning("Barcode scanner just disconnected")

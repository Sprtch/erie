from erie.devices.message import BarcodeMessage
from erie.devices.device import DeviceWrapper
from evdev import InputDevice, categorize, ecodes
import os
import time

class InputDeviceWrapper(DeviceWrapper):
    # Make the keyboard mapping between the scandata received from evdev and the
    # actual value on the keyboard (should be qwerty).
    KEYBOARD_TRANSLATE = {
        # Keyboard code: actual number
        'LEFTSHIFT': '',
        'SLASH': '/',
    }

    def __init__(self, name, path=None, deviceid=None, redis=None):
        super().__init__("EVDEV", name)

        if not (path or deviceid):
            self.error("Must specify a path or device id")

        if deviceid:
            self.path = "/dev/input/by-id/%s" % (deviceid)
        else:
            self.path = path

        self.redis = redis
        self._dev = None

    def present(self):
        if os.path.exists(self.path):
            self.info("Barcode scanner found")
            self._dev = InputDevice(self.path)
            self._dev.grab()
        elif self._dev:
            self._dev.ungrab() # Test this case
            self._dev = None
            self.warning("Barcode disconnected")
        else:
            self.warning("Still no barcode scanner plugged")

        return self._dev is not None

    def _read_loop(self):
        barcode = ''
        try:
            for ev in self._dev.read_loop():
                if ev.type == ecodes.EV_KEY:
                    data = categorize(ev)
                    if (data.keystate == 0):
                        key = ecodes.KEY[data.scancode][4:] # Remove the "KEY_" default character of ecode to only get the key
                        key = InputDeviceWrapper.KEYBOARD_TRANSLATE.get(key, key)
                        if (key == None and barcode) or key == 'ENTER':
                            yield barcode
                            barcode = ''
                        elif len(key):
                            barcode += str(key)
        except OSError:
            self.warning("Barcode scanner just disconnected")

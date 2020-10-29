from erie.logger import logger
from evdev import InputDevice, categorize, ecodes
import os
import time

class InputDeviceWrapper:
    # Make the keyboard mapping between the scandata received from evdev and the
    # actual value on the keyboard (should be qwerty).
    KEYBOARD_TRANSLATE = {
        # Keyboard code: actual number
        'LEFTSHIFT': '',
        'SLASH': '/',
    }

    def __init__(self, name, path=None, deviceid=None, redis=None):
        if not (path or deviceid):
            logger.error("[EVDEV:%s] Must specify a path or device id" % (name))

        if deviceid:
            self.path = "/dev/input/by-id/%s" % (deviceid)
        else:
            self.path = path

        self.name = name
            
        self.redis = redis
        self._dev = None

    def present(self):
        if os.path.exists(self.path):
            logger.info("[EVDEV] Barcode scanner found")
            self._dev = InputDevice(self.path)
            self._dev.grab()
        elif self._dev:
            self._dev.ungrab() # Test this case
            self._dev = None
            logger.warning("[EVDEV] Barcode disconnected")
        else:
            logger.warning("Still no barcode scanner plugged")

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
            logger.warning("Barcode scanner just disconnected")

    def read_loop(self):
        while True:
            if not self.present():
                time.sleep(5)
                continue
            for x in self._read_loop():
                yield x

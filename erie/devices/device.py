from erie.logger import logger
from erie.devices.message import BarcodeMessage
import time

class DeviceWrapper:
    def __init__(self, devicetype, name):
        self._device_type = devicetype
        self.name = name

    def info(self, msg):
        logger.info("[%s:%s] %s" % (self._device_type, self.name, msg))

    def warning(self, msg):
        logger.warning("[%s:%s] %s" % (self._device_type, self.name, msg))

    def error(self, msg):
        logger.error("[%s:%s] %s" % (self._device_type, self.name, msg))

    def present(self):
        raise NotImplementedError

    def _read_loop(self):
        raise NotImplementedError

    def read_loop(self):
        while True:
            if not self.present():
                time.sleep(5)
                continue
            for x in self._read_loop():
                yield x

from erie.logger import logger
from erie.message import BarcodeMessage
import time

class DeviceWrapper:
    def __init__(self, devicetype, name, redis):
        self._device_type = devicetype
        self.name = name
        self.redis = redis

    def debug(self, msg):
        logger.debug("[%s:%s] %s" % (self._device_type, self.name, msg))

    def info(self, msg):
        logger.info("[%s:%s] %s" % (self._device_type, self.name, msg))

    def warning(self, msg):
        logger.warning("[%s:%s] %s" % (self._device_type, self.name, msg))

    def error(self, msg):
        logger.error("[%s:%s] %s" % (self._device_type, self.name, msg))

    def present(self):
        raise NotImplementedError

    def retrieve(self):
        raise NotImplementedError

    def read_loop(self):
        while True:
            if not self.present():
                time.sleep(5)
                continue
            for x in self.retrieve():
                yield BarcodeMessage(x, self.name, self.redis)

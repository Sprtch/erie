from despinassy.ipc import create_nametuple
from erie.message import Message
import logging
import time

logger = logging.getLogger(__name__)


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
                yield Message(barcode=x, name=self.name, redis=self.redis)

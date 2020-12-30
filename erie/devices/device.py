from despinassy.ipc import create_nametuple
from erie.message import Message
from despinassy.Scanner import ScannerTypeEnum
import dataclasses
import logging
import time

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class DeviceWrapper:
    name: str
    redis: str

    def get_type(self):
        return self.DEVICE_TYPE

    def debug(self, msg):
        logger.debug("[%s:%s] %s" % (self._device_type, self.name, msg))

    def info(self, msg):
        logger.info("[%s:%s] %s" % (self._device_type, self.name, msg))

    def warning(self, msg):
        logger.warning("[%s:%s] %s" % (self._device_type, self.name, msg))

    def error(self, msg):
        logger.error("[%s:%s] %s" % (self._device_type, self.name, msg))

    def export_config(self):
        raise NotImplementedError

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

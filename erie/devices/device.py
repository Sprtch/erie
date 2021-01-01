from despinassy.ipc import create_nametuple
from erie.message import DevicePresentMessage, DeviceNotPresentMessage, Message
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
        logger.debug("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def info(self, msg):
        logger.info("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def warning(self, msg):
        logger.warning("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def error(self, msg):
        logger.error("[%s:%s] %s" % (str(self.get_type()), self.name, msg))

    def export_config(self):
        raise NotImplementedError

    def present(self):
        raise NotImplementedError

    def retrieve(self):
        raise NotImplementedError

    def read_loop(self):
        while True:
            if not self.present():
                yield DeviceNotPresentMessage()
                time.sleep(5)
            else:
                yield DevicePresentMessage()
                for x in self.retrieve():
                    yield Message(barcode=x, name=self.name, redis=self.redis)

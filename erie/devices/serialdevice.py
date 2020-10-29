from erie.logger import logger
import serial
import os
import time

class SerialWrapper:
    def __init__(self, name, path=None, deviceid=None, redis=None):
        if not (path or deviceid):
            logger.error("[SER:%s] Must specify a path or device id" % (name))

        if deviceid:
            self.path = "/dev/serial/by-id/%s" % (deviceid)
        else:
            self.path = path
            
        self.redis = redis
        self._dev = None

    def present(self):
        if os.path.exists(self.path):
            logger.info("[SERIAL] Barcode scanner found")
            self._dev = serial.Serial(self.path, 9600, timeout=1)
        else:
            logger.warning("[SERIAL] Still no barcode scanner found")
            self._dev = None

        return self._dev is not None

    def _read_loop(self):
        try:
            while 1:
                line = self._dev.readline().decode('utf-8').strip()
                if line:
                    yield line
        except serial.serialutil.SerialException as e:
            logger.warning(e)

    def read_loop(self):
        barcode = ''
        while True:
            if not self.present():
                time.sleep(5)
                continue
            for x in self._read_loop():
                yield x

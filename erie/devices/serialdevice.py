from erie.logger import logger
import serial
import os
import time

class SerialWrapper:
    def __init__(self, path):
        self.path = path 
        self.dev = path 

    def present(self):
        if os.path.exists(self.path):
            logger.info("[SERIAL] Barcode scanner found")
            self.dev = serial.Serial(self.path, 9600, timeout=1)
        else:
            logger.warning("[SERIAL] Still no barcode scanner found")
            self.dev = None

        return self.dev is not None

    def _read_loop(self):
        try:
            while 1:
                line = self.dev.readline().decode('utf-8').strip()
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

from erie.devices.device import DeviceWrapper
import serial
import os

class SerialWrapper(DeviceWrapper):
    def __init__(self, name, redis, path=None, deviceid=None):
        super().__init__("SERIAL", name, redis)

        if not (path or deviceid):
            self.error("Must specify a path or device id")

        if deviceid:
            self.path = "/dev/serial/by-id/%s" % (deviceid)
        else:
            self.path = path
            
        self._dev = None

    def present(self):
        if os.path.exists(self.path):
            self.info("Barcode scanner found")
            self._dev = serial.Serial(self.path, 9600, timeout=1)
        else:
            self.warning("Still no barcode scanner found")
            self._dev = None

        return self._dev is not None

    def retrieve(self):
        try:
            while 1:
                line = self._dev.readline().decode('utf-8').strip()
                if line:
                    yield line
        except serial.serialutil.SerialException as e:
            self.error(e)

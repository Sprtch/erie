from daemonize import Daemonize
from evdev import InputDevice, categorize, ecodes
import os
import time
import logging
import argparse
import redis
import serial
import queue, threading

APPNAME = "erie"
REDIS_PUB_CHAN = "victoria"
USB_SCANNER_PATH = "/dev/input/by-id/usb-Belon.cn_2.4G_Wireless_Device_Belon_Smart-event-kbd"
SERIAL_SCANNER_PATH = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9UXOL6H-if00-port0"

r = redis.Redis(host='localhost', port=6379, db=0)
p = r.pubsub()

logger = logging

class InputDeviceWrapper:
    # Make the keyboard mapping between the scandata received from evdev and the
    # actual value on the keyboard (should be qwerty).
    KEYBOARD_TRANSLATE = {
        # Keyboard code: actual number
        'LEFTSHIFT': '',
        'SLASH': '/',
    }

    def __init__(self, path):
        self.path = path
        self.dev = None

    def present(self):
        if os.path.exists(self.path):
            logger.info("[EVDEV] Barcode scanner found")
            self.dev = InputDevice(self.path)
            self.dev.grab()
        elif self.dev:
            self.dev.ungrab() # Test this case
            self.dev = None
            logger.warning("[EVDEV] Barcode disconnected")
        else:
            logger.warning("Still no barcode scanner plugged")

        return self.dev is not None

    def _read_loop(self):
        barcode = ''
        try:
            for ev in self.dev.read_loop():
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
        barcode = ''
        while True:
            if not self.present():
                time.sleep(5)
                continue
            for x in self._read_loop():
                yield x

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

def send_to_print(barcode):
    logger.info("Scanned '%s'" % (barcode))
    try: 
        r.publish(REDIS_PUB_CHAN, '{"name": "%s", "barcode": "%s"}' % (barcode, barcode))
    except redis.ConnectionError as e:
        logger.error(e)

def gen_multiplex(genlist):
    item_q = queue.Queue()
    def run_one(source):
        for item in source: item_q.put(item)

    def run_all():
        thrlist = []
        for source in genlist:
            t = threading.Thread(target=run_one,args=(source,))
            t.start()
            thrlist.append(t)
        for t in thrlist: t.join()
        item_q.put(StopIteration)

    threading.Thread(target=run_all).start()
    while True:
        item = item_q.get()
        if item is StopIteration: return
        yield item

def barcode_scanner_listener(devlist):
    for barcode in gen_multiplex(map(lambda x: x.read_loop(), devlist)):
        send_to_print(barcode)

def main():
    barcode_scanner_listener((InputDeviceWrapper(USB_SCANNER_PATH), SerialWrapper(SERIAL_SCANNER_PATH)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--no-daemon', dest='nodaemon', action='store_true', help='Does not start the program as a daemon')
    parser.add_argument('--logfile', dest='logfile', type=str, help='Log destination', default=("/var/log/%s.log" % APPNAME))
    parser.add_argument('--pid', dest='pid', type=str, help='Pid destination', default=("/var/run/%s.pid" % APPNAME))

    args = parser.parse_args()

    if args.nodaemon:
        logger.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logger.DEBUG)
        main()
    else:
        logger = logger.getLogger(__name__)
        logger.setLevel(logger.DEBUG)
        logger.propagate = False

        fh = logger.FileHandler(args.logfile, "w")
        fh.setLevel(logger.DEBUG)
        formatter = logger.Formatter(fmt='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        fh.setFormatter(formatter)

        logger.addHandler(fh)
        keep_fds = [fh.stream.fileno()]

        daemon = Daemonize(app=APPNAME, logger=logger, pid=args.pid, action=main, keep_fds=keep_fds)
        daemon.start()

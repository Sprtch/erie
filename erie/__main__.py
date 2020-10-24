from daemonize import Daemonize
from evdev import InputDevice, categorize, ecodes
import os
import time
import logging
import argparse
import redis

APPNAME = "erie"
REDIS_PUB_CHAN = "victoria"
USB_SCANNER_PATH = "/dev/input/by-id/usb-Belon.cn_2.4G_Wireless_Device_Belon_Smart-event-kbd"

r = redis.Redis(host='localhost', port=6379, db=0)
p = r.pubsub()

# Make the keyboard mapping between the scandata received from evdev and the
# actual value on the keyboard (should be qwerty).
KEYBOARD_TRANSLATE = {
    # Keyboard code: actual number
    'LEFTSHIFT': '',
    'SLASH': '/',
}

logger = logging

class Scanner:
    def __init__(self, path):
        self.path = path
        self.dev = None

    def present(self):
        if os.path.exists(USB_SCANNER_PATH):
            logger.info("Plugged barcode scanner")
            self.dev = InputDevice(USB_SCANNER_PATH)
        else:
            logger.warning("Still no barcode scanner plugged")
            self.dev = None

        return self.dev is not None

    def grab(self):
        self.dev.grab()

    def ungrab(self):
        self.dev.ungrab()

    def read_loop(self):
        return self.dev.read_loop()

def send_to_print(barcode):
    logger.info("Scanned '%s'" % (barcode))
    try: 
        r.publish(REDIS_PUB_CHAN, '{"name": "%s", "barcode": "%s"}' % (barcode, barcode))
    except redis.ConnectionError as e:
        logger.error(e)

def barcode_scanner_listener(dev):
    barcode = ''
    # g = usb_scanner_checker()
    while True:
        if not dev.present():
            time.sleep(5)
            continue
        try:
            dev.grab()
            for ev in dev.read_loop():
                if ev.type == ecodes.EV_KEY:
                    data = categorize(ev)
                    if (data.keystate == 0):
                        key = ecodes.KEY[data.scancode][4:] # Remove the "KEY_" default character of ecode to only get the key
                        key = KEYBOARD_TRANSLATE.get(key, key)
                        if (key == None and barcode) or key == 'ENTER':
                            send_to_print(barcode)
                            barcode = ''
                        elif len(key):
                            barcode += str(key)
            dev.ungrab()
        except OSError:
            logger.warning("Barcode scanner just disconnected")

def main():
    barcode_scanner_listener(Scanner(USB_SCANNER_PATH))

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

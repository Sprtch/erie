from time import sleep
from daemonize import Daemonize
from evdev import InputDevice, categorize, ecodes
import logging
import argparse
import redis

pid = "/tmp/erie.pid"
r = redis.Redis(host='localhost', port=6379, db=0)
p = r.pubsub()
# logging.basicConfig(filename='/var/log/erie.log', level=logging.DEBUG)

# Make the keyboard mapping between the scandata received from evdev and the
# actual value on the keyboard (should be qwerty).
KEYBOARD_TRANSLATE = {
    # Keyboard code: actual number
    'LEFTSHIFT': '',
    'SLASH': '/',
}

def usb_scanner_checker():
    USB_SCANNER_PATH = "/dev/input/by-id/usb-Belon.cn_2.4G_Wireless_Device_Belon_Smart-event-kbd"
    dev = None
    while True:
        if os.path.exists(USB_SCANNER_PATH):
            logging.info("Plugged barcode scanner")
            dev = InputDevice(USB_SCANNER_PATH)
        else:
            logging.warning("Still no barcode scanner plugged")
            dev = None

        yield dev

async def input_listener():
    while True:
        barcode = await ainput(">>>")
        r.publish('printer', '{"name": "%s", "barcode": "%s"}' % (barcode, barcode))


async def barcode_scanner_listener():
    barcode = ''
    g = usb_scanner_checker()
    for dev in g:
        if dev is None:
            await asyncio.sleep(5)
            continue
        try:
            dev.grab()
            async for ev in dev.async_read_loop():
                if ev.type == ecodes.EV_KEY:
                    data = categorize(ev)
                    if (data.keystate == 0):
                        key = ecodes.KEY[data.scancode][4:] # Remove the "KEY_" default character of ecode to only get the key
                        key = KEYBOARD_TRANSLATE.get(key, key)
                        if (key == None and barcode) or key == 'ENTER':
                            r.publish('printer', '{"name": "%s", "barcode": "%s"}' % (barcode, barcode))
                            barcode = ''
                        elif len(key):
                            barcode += str(key)
            dev.ungrab()
        except OSError:
            logging.warning("Barcode scanner just disconnected")


def main():
    loop = asyncio.get_event_loop()

    # loop.create_task(barcode_scanner_listener())
    # loop.create_task(input_listener())

    try:
        loop.run_until_complete(input_listener())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--no-daemon', dest='nodaemon', action='store_true', help='Does not start the program as a daemon')
    args = parser.parse_args()

    if args.nodaemon:
        main()
    else:
        daemon = Daemonize(app="erie", pid=pid, action=main)
        daemon.start()

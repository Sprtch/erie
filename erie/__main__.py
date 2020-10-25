from erie.config import Config
from erie.logger import logger
from erie.devices.inputdevice import InputDeviceWrapper
from erie.devices.serialdevice import SerialWrapper
from daemonize import Daemonize
import os
import argparse
import redis
import queue, threading

APPNAME = "erie"
REDIS_PUB_CHAN = "victoria"
USB_SCANNER_PATH = "/dev/input/by-id/usb-Belon.cn_2.4G_Wireless_Device_Belon_Smart-event-kbd"
SERIAL_SCANNER_PATH = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9UXOL6H-if00-port0"

r = redis.Redis(host='localhost', port=6379, db=0)
p = r.pubsub()

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

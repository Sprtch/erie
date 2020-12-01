from erie.config import Config
from erie.logger import logger
from erie.processor import Processor
from erie.devices.inputdevice import InputDeviceWrapper
from erie.devices.serialdevice import SerialWrapper
from erie.db import db, init_db
from daemonize import Daemonize
import os
import argparse
import queue, threading
import json

APPNAME = "erie"

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

def main(conf):
    for _ in gen_multiplex(map(lambda x: x.read(), map(lambda x: Processor(x), conf.devices))):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--no-daemon', dest='nodaemon', action='store_true', help='Does not start the program as a daemon')
    parser.add_argument('--logfile', dest='logfile', type=str, help='Log destination', default=("/var/log/%s.log" % APPNAME))
    parser.add_argument('--debug', dest='debuglevel', action='store_true', help='Set the log level to show debug messages')
    parser.add_argument('--pid', dest='pid', type=str, help='Pid destination', default=("/var/run/%s.pid" % APPNAME))
    parser.add_argument('-c', '--config', dest='config', type=str, help='Config file location', default=("./config.yaml"))

    args = parser.parse_args()

    conf = Config(args.config, debug=args.debuglevel)
    init_db(conf.db)

    loglevel = logger.DEBUG if args.debuglevel else logger.INFO
    if args.nodaemon:
        logger.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=loglevel)
        main(conf)
    else:
        logger = logger.getLogger(__name__)
        logger.setLevel(loglevel)
        logger.propagate = False

        fh = logger.FileHandler(args.logfile, "w")
        fh.setLevel(loglevel)
        formatter = logger.Formatter(fmt='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        fh.setFormatter(formatter)

        logger.addHandler(fh)
        keep_fds = [fh.stream.fileno()]

        daemon = Daemonize(app=APPNAME, logger=logger, pid=args.pid, action=lambda: main(conf), keep_fds=keep_fds)
        daemon.start()

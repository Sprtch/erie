from erie.config import Config
from erie.logger import logger
from erie.processor import Processor
from erie.db import init_db
from daemonize import Daemonize
import logging
import argparse
import threading

APPNAME = "erie"


def main(conf):
    thrlist = []
    for dev in conf.devices:
        t = threading.Thread(target=Processor(dev).read)
        t.start()
        thrlist.append(t)

    for t in thrlist:
        t.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--no-daemon',
                        dest='nodaemon',
                        action='store_true',
                        help='Does not start the program as a daemon')
    parser.add_argument('--logfile',
                        dest='logfile',
                        type=str,
                        help='Log destination',
                        default=("/var/log/%s.log" % APPNAME))
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='Set the log level to show debug messages')
    parser.add_argument('--pid',
                        dest='pidfile',
                        type=str,
                        help='Pid destination',
                        default=("/var/run/%s.pid" % APPNAME))
    parser.add_argument('-c',
                        '--config',
                        dest='config',
                        type=str,
                        help='Config file location',
                        default=("./config.yaml"))

    args = parser.parse_args()
    configfile = vars(args).pop('config')
    arguments = vars(args)

    conf = Config.from_yaml_file(configfile, **arguments)

    loglevel = logger.DEBUG if conf.debug else logger.INFO
    if conf.nodaemon:
        logger.basicConfig(format='[%(asctime)s] %(message)s',
                           datefmt='%m/%d/%Y %I:%M:%S %p',
                           level=loglevel)
        main(conf)
    else:
        logger = logger.getLogger(__name__)
        logger.setLevel(loglevel)
        logger.propagate = False

        fh = logging.FileHandler(conf.logfile, "w")
        fh.setLevel(loglevel)
        formatter = logging.Formatter(fmt='[%(asctime)s] %(message)s',
                                      datefmt='%m/%d/%Y %I:%M:%S %p')
        fh.setFormatter(formatter)

        logger.addHandler(fh)
        keep_fds = [fh.stream.fileno()]

        daemon = Daemonize(app=APPNAME,
                           logger=logger,
                           pid=conf.pidfile,
                           action=lambda: main(conf),
                           keep_fds=keep_fds)
        daemon.start()

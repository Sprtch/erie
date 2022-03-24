from erie.config import Config
from erie.processor import Processor
from erie.db import init_db, db
import sys
import signal
from lockfile import FileLock
import daemon
import logging
import argparse
import threading


def program_cleanup(signal, frame):
    logger.info("Terminating the program from signal (%i)" % (signal))
    # PrinterTable.query.update(dict(hidden=True, available=False))
    db.session.commit()
    exit()

def main(conf):
    thrlist = []
    init_db(conf.database)

    for dev in conf.devices:
        proc = Processor(dev)
        t = threading.Thread(target=proc.read)
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
                        default=None)
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='Set the log level to show debug messages')
    parser.add_argument('--pid',
                        dest='pidfile',
                        type=str,
                        help='Pid destination',
                        default=None)
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
 
    logger = logging.getLogger(Config.APPNAME)
    ctx = daemon.DaemonContext(
            pidfile=FileLock(conf.pidfile) if conf.pidfile else None,
            files_preserve=[i.stream for i in logger.handlers if hasattr(i, 'baseFilename')],
            detach_process=not args.nodaemon,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            signal_map={
                signal.SIGTERM: program_cleanup,
                signal.SIGINT: program_cleanup,
            })
    # TODO error and stdout to file ?

    with ctx:
        main(conf)

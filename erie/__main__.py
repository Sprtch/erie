from erie.config.config import Config
from erie.config.util import generate_devices_from_config
from erie.device import Device
import sys
import signal
from lockfile import FileLock
import daemon
import logging
import argparse
import threading
from typing import List


logger = logging.getLogger()
stop_event = threading.Event()
devices: List[Device] = []


def setup_logging(logfile=None, debug=False, nodaemon=False):
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    logger.handlers = []

    handlers = []

    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Always keep stdout in non-daemon mode
    if nodaemon or not logfile:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

    for h in handlers:
        logger.addHandler(h)

    return handlers


def program_cleanup(signum, frame):
    logger.info(f"Received signal ({signum}), shutting down...")
    stop_event.set()

    # Force disconnect immediately (important if read() blocks)
    for dev in devices:
        try:
            dev.disconnect()
        except Exception:
            logger.exception("Error during disconnect in signal handler")


def worker(dev: Device):
    try:
        while not stop_event.is_set():
            dev.read()  # must be non-blocking or interruptible
    except Exception:
        logger.exception("Worker error")
    finally:
        try:
            dev.disconnect()
        except Exception:
            logger.exception("Error during final disconnect")


def main():
    threads = []

    for dev in devices:
        t = threading.Thread(target=worker, args=(dev,), daemon=False)
        t.start()
        threads.append(t)

    # Wait for shutdown
    try:
        for t in threads:
            t.join()
    finally:
        # Ensure cleanup even if something goes wrong
        logger.info("Final cleanup: disconnecting all devices")
        for dev in devices:
            try:
                dev.disconnect()
            except Exception:
                logger.exception("Error during final cleanup disconnect")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--no-daemon", dest="nodaemon", action="store_true")
    parser.add_argument("--logfile", type=str, default=None)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--pid", dest="pidfile", type=str, default=None)
    parser.add_argument("-c", "--config", type=str, default="./config.yaml")

    args = parser.parse_args()
    configfile = vars(args).pop("config")
    arguments = vars(args)

    config = Config.from_yaml(configfile, **arguments)
    devices = generate_devices_from_config(config)

    handlers = setup_logging(args.logfile, args.debug, args.nodaemon)

    signal.signal(signal.SIGTERM, program_cleanup)
    signal.signal(signal.SIGINT, program_cleanup)

    ctx = daemon.DaemonContext(
        pidfile=FileLock(config.pidfile) if config.pidfile else None,
        detach_process=not args.nodaemon,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        files_preserve=[
            h.stream for h in handlers if hasattr(h, "stream")
        ],
    )

    if args.nodaemon:
        logger.info("Starting in non-daemon mode")
        main()
    else:
        with ctx:
            logger.info("Starting in daemon mode")
            main()

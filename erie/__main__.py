from erie.config.config import Config
from erie.config.util import generate_devices_from_config
from erie.daemon.runner import run
import sys
import logging
import argparse

logger = logging.getLogger()


def setup_logging(logfile=None, debug=False, nodaemon=False):
    """Return handler after setting up logging."""
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

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


def parse_args() -> argparse.Namespace:
    """Return argparse namespace."""
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--no-daemon", dest="nodaemon", action="store_true", default=None)
    parser.add_argument("--logfile", type=str, default=None)
    parser.add_argument("--debug", action="store_true", default=None)
    parser.add_argument("--pid", dest="pidfile", type=str, default=None)
    parser.add_argument("-c", "--config", type=str, default="./config.yaml")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    configfile = vars(args).pop("config")
    arguments = vars(args)

    config = Config.from_yaml(configfile, **arguments)
    devices = generate_devices_from_config(config)
    handlers = setup_logging(config.logfile, config.debug, config.nodaemon)

    run(config, devices, handlers)

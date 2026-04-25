import sys
import signal
import logging
import threading
from typing import Iterable
from lockfile import FileLock
import daemon

from erie.config.config import Config
from erie.device import Device
from erie.utils.functional import attempt_all

logger = logging.getLogger(__name__)


def make_signal_handler(
    stop_event: threading.Event,
    devices: Iterable[Device],
) -> signal.Handlers:
    """Return a signal handler closed over stop_event and devices."""

    def handler(signum, frame) -> None:
        logger.info("Signal %s received: shutting down", signum)
        stop_event.set()
        attempt_all(dev.disconnect for dev in devices)

    return handler


def build_daemon_context(config: Config, log_handlers) -> daemon.DaemonContext:
    return daemon.DaemonContext(
        pidfile=FileLock(config.pidfile) if config.pidfile else None,
        detach_process=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        files_preserve=[h.stream for h in log_handlers if hasattr(h, "stream")],
    )


def run(config: Config, devices: Iterable[Device], log_handlers) -> None:
    from erie.daemon.supervisor import run_workers

    stop_event = threading.Event()
    handler = make_signal_handler(stop_event, devices)

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    if config.nodaemon:
        logger.info("Starting in non-daemon mode")
        run_workers(devices, stop_event)
    else:
        with build_daemon_context(config, log_handlers):
            logger.info("Starting in daemon mode")
            run_workers(devices, stop_event)

import threading
import logging
from typing import Callable, Iterable
from erie.device import Device
from erie.utils.functional import attempt, attempt_all

logger = logging.getLogger(__name__)


def make_worker(device: Device, stop_event: threading.Event) -> Callable[[], None]:
    """Return a zero-argument worker closure over a single device."""

    def worker() -> None:
        logger.info("Worker started: %s", device)
        attempt(lambda: device.read_loop(stop_event), label=f"read_loop({device})")
        attempt(device.disconnect, label=f"disconnect({device})")

    return worker


def run_workers(
    devices: Iterable[Device],
    stop_event: threading.Event,
) -> None:
    """Spawn device thread and wait to finish.

    Spawn one daemon-False thread per device, block until all finish,
    then guarantee a final disconnect pass on every device.
    """
    workers = [make_worker(dev, stop_event) for dev in devices]

    threads = [
        threading.Thread(target=w, daemon=False, name=f"worker-{i}") for i, w in enumerate(workers)
    ]

    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
    finally:
        logger.info("Supervisor: final disconnect pass")
        attempt_all(dev.disconnect for dev in devices)

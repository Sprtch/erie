import dataclasses
import logging
import os
import select
from typing import Optional

import evdev
from evdev.ecodes import EV_KEY

from erie.reader.file import FileStreamReader
from erie.schema.type import ScannerTypeEnum

logger = logging.getLogger(__name__)


class EvdevWrapper:
    def __init__(self, device):
        self._dev = device

    @property
    def closed(self):
        return not self._dev.fd >= 0

    def fileno(self):
        return self._dev.fd

    def read_events(self):
        return self._dev.read()

    def open(self):
        self._dev.grab()

    def close(self):
        self._dev.ungrab()
        self._dev.close()


@dataclasses.dataclass
class EvdevReader(FileStreamReader):
    """Reader device reading from 'evdev' linux device."""

    deviceid: Optional[str] = None

    KEYBOARD_TRANSLATE = {
        "LEFTSHIFT": "",
        "SEMICOLON": ":",
        "SLASH": "/",
        "MINUS": "-",
        "DOT": ".",
        "COMMA": ",",
    }

    def __post_init__(self):
        if not (self.path or self.deviceid):
            logger.error("Must specify a path or device id")

        if self.deviceid:
            self.path = f"/dev/input/by-id/{self.deviceid}"

        self._barcode = ""
        self._pending_barcode = None

    @property
    def type(self):
        return ScannerTypeEnum.EVDEV

    def connect(self):
        logger.debug(f"[{self.__class__.__name__}] Opening '{self.path}'")
        if self.present():
            dev = evdev.InputDevice(self.path)
            self.io = EvdevWrapper(dev)
            self.io.open()

    def read(self) -> str | None:
        if self._pending_barcode is not None:
            barcode = self._pending_barcode
            self._pending_barcode = None
            return barcode

        ready, _, _ = select.select([self.io], [], [], self.poll_timeout)

        if not ready:
            return None

        try:
            events = self.io.read_events()
        except OSError:
            logger.warning("Barcode scanner just disconnected")
            return None

        for ev in events:
            if ev.type == EV_KEY:
                data = evdev.categorize(ev)
                if data.keystate == 0:
                    key = evdev.KEY[data.scancode][4:]
                    key = self.KEYBOARD_TRANSLATE.get(key, key)
                    if key is None and self._barcode:
                        self._pending_barcode = self._barcode
                        self._barcode = ""
                        return self._pending_barcode
                    elif key == "ENTER":
                        if self._barcode:
                            self._pending_barcode = self._barcode
                            self._barcode = ""
                            return self._pending_barcode
                    elif len(key):
                        self._barcode += str(key)

        return None

    # def retrieve(self, stop_event: threading.Event = None):
    #     # TODO Remove this implementation and simplify previous one.
    #     barcode = ""
    #     try:
    #         for ev in self._dev.read_loop():
    #             if stop_event is not None and stop_event.is_set():
    #                 logger.debug("[%s] stop_event set: exiting", self.type)
    #                 return
    #
    #             if ev.type == EV_KEY:
    #                 data = evdev.categorize(ev)
    #                 if data.keystate == 0:
    #                     key = KEY[data.scancode][4:]
    #                     key = Evdev.KEYBOARD_TRANSLATE.get(key, key)
    #                     if (key is None and barcode) or key == "ENTER":
    #                         yield barcode
    #                         barcode = ""
    #                     elif len(key):
    #                         barcode += str(key)
    #     except OSError:
    #         logger.warning("Barcode scanner just disconnected")

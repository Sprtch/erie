"""Evdev input device reader for barcode scanners.

Reads keyboard-style input events from Linux evdev devices and translates
keycodes into barcode strings.
"""

import dataclasses
import select
from typing import Optional

import evdev
from evdev.ecodes import EV_KEY

from erie.reader.file import FileStreamReader
from erie.schema.type import ScannerTypeEnum


class EvdevWrapper:
    """Thin wrapper around an evdev.InputDevice providing an IOBase-like interface."""

    def __init__(self, device):
        self._dev = device

    @property
    def closed(self):
        """Return True if the underlying device file descriptor is closed."""
        return not self._dev.fd >= 0

    def fileno(self):
        """Return the file descriptor of the underlying device."""
        return self._dev.fd

    def read_events(self):
        """Return pending input events from the device."""
        return self._dev.read()

    def open(self):
        """Grab exclusive access to the device so other consumers cannot read it."""
        self._dev.grab()

    def close(self):
        """Release and close the underlying device."""
        self._dev.ungrab()
        self._dev.close()


@dataclasses.dataclass
class EvdevReader(FileStreamReader):
    """Reader device reading from 'evdev' linux device.

    Translates keyboard key-up events into barcode characters. Special keys
    (SHIFT, ENTER, punctuation) are mapped via KEYBOARD_TRANSLATE. A barcode
    is emitted when ENTER is pressed or an unmapped key is encountered.
    """

    device_id: Optional[str] = None

    KEYBOARD_TRANSLATE = {
        "LEFTSHIFT": "",
        "SEMICOLON": ":",
        "SLASH": "/",
        "MINUS": "-",
        "DOT": ".",
        "COMMA": ",",
    }

    def __post_init__(self):
        super().__post_init__()
        if not (self.path or self.device_id):
            self.logger.error("Must specify a path or device id")

        if self.device_id:
            self.path = f"/dev/input/by-id/{self.device_id}"

        self._barcode = ""
        self._pending_barcode = None

    @property
    def type(self):
        return ScannerTypeEnum.EVDEV

    def connect(self):
        """Open the evdev device and grab exclusive access."""
        self.logger.debug(f"Opening '{self.path}'")
        if self.present():
            dev = evdev.InputDevice(self.path)
            self.io = EvdevWrapper(dev)
            self.io.open()

    def read(self) -> str | None:
        """Read key events and return a completed barcode string, or None.

        Key-up events are translated to characters and accumulated into a
        barcode buffer. Returns the buffered barcode when ENTER is pressed
        or an unmapped key is encountered, then resets the buffer.
        """
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
            self.logger.warning("Barcode scanner just disconnected")
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

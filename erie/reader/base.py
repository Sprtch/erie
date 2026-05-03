from abc import ABC, abstractmethod
from typing import Iterator
import dataclasses
import logging
import threading
import time


@dataclasses.dataclass
class Reader(ABC):
    """Abstract base class for input sources that read barcode scanner data.

    A Reader wraps a physical or virtual input device (serial port, evdev,
    stdin, Redis channel) and exposes a uniform iterator interface.  The
    main entry point is :meth:`retrieve`, which yields complete barcode
    strings as they arrive.

    Subclass contract:
      - Implement :meth:`type` (property): return the device type enum.
      - Implement :meth:`present`: return whether the device node exists.
      - Implement :meth:`read`: non-blocking read of one line/barcode.
      - Override :meth:`connect` / :meth:`disconnect` to open/close the
          underlying resource.

    Lifecycle::
        with reader:          # calls connect()
            for line in reader.retrieve(stop_event):
                process(line)
        # calls disconnect() on exit
    """

    def __post_init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.type}")

    @property
    @abstractmethod
    def type(self):
        """Return the :class:`~erie.schema.type.ScannerTypeEnum` for this reader.

        Used for logging and identifying the reader implementation.
        """
        ...

    # def export_config(self) -> str:
    #     """Return a string in JSON format of the configuration specificity of the current reading device.
    #
    #     This function needs to be implemented in the specialized class.
    #     """
    #     raise NotImplementedError

    @abstractmethod
    def present(self) -> bool:
        """Whether or not the reading device is currently available.

        This function needs to be implemented in the specialized class.
        """
        ...

    def connected(self) -> bool:
        """Whether or not the reading device is currently connected.

        By default is the same as `present` method.
        """
        return self.present()

    @abstractmethod
    def read(self) -> str | None:
        """Read content in child class (non blocking).

        This function needs to be implemented in the specialized class.
        """
        ...

    def retrieve(self, stop_event: threading.Event, poll_timeout: float = 1.0) -> Iterator[str]:
        """Yield barcodes from this reader until disconnected or *stop_event* is set.

        Calls :meth:`read` in a loop.
        Returns ``None`` means no data yet; the loop sleeps briefly and retries.
        Returns a non-empty string means a complete barcode was received.

        This is the main public API.
        It is consumed by :meth:`erie.device.device.ErieDevice.read_loop`.

        :param stop_event: Threading event to signal a graceful shutdown.
        :param poll_timeout: Unused in base class; available for subclasses.
        """
        while self.connected():
            # Check stop_event between polls so we exit cleanly even when
            # the device is stopped but no new data has arrived yet.
            if stop_event is not None and stop_event.is_set():
                self.logger.debug("stop_event set: exiting")
                return

            content = self.read()
            if content is None:
                time.sleep(0.1)
                continue

            yield content.rstrip("\n")

    def connect(self):
        """Open the underlying device resource.

        Subclasses should override to acquire handles (open files, subscribe
        to channels, etc.).  The base class is a no-op.
        """
        self.logger.debug("Connecting")

    def disconnect(self):
        """Close the underlying device resource.

        Subclasses should override to release handles.  The base class is a
        no-op.
        """
        self.logger.debug("Disconnecting")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return self

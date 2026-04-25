from abc import ABC, abstractmethod
from typing import Optional, Iterator, Any
import dataclasses
import logging
import threading
# import time
# import queue

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Reader(ABC):
    """A `Reader` is a device that forware message events.

    Typically this will be assigned to a 'barcode scanning' device but can
    be generalized to any type of device tthat can read inputs.
    """

    @property
    @abstractmethod
    def type(self): ...

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
        while self.connected():
            # Check stop_event between polls so we exit cleanly even when
            # the device is stopped but no new data has arrived yet.
            if stop_event is not None and stop_event.is_set():
                logger.debug("[%s] stop_event set: exiting", self.type)
                return

            content = self.read()
            if content is None:
                continue

            yield content.rstrip("\n")

    def connect(self):
        logger.debug("[%s] Connecting", self.type)

    def disconnect(self):
        logger.debug("[%s] Disconnecting", self.type)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return self


# class ReaderBlocking(Reader):
#     """Blocking IO class.
#
#     Children class needs to define the 'type', 'read' & 'present' methods.
#     """
#
#     @abstractmethod
#     def read(self):
#         """Blocking reading call."""
#         ...
#
#     def retrieve(self):
#         self,
#         stop_event: Optional[threading.Event] = None,
#         poll_timeout: float = 1.0,
#     ) -> Iterator[str]:
#         q: queue.Queue = queue.Queue()
#
#         def _pump() -> None:
#             try:
#                 while not stop_event.is_set():
#                     item = self.read()          # may block indefinitely
#                     if stop_event.is_set():     # re-check after unblocking
#                         break
#                     q.put(item)
#             except Exception as exc:
#                 q.put(exc)                      # propagate errors to consumer
#             finally:
#                 q.put(_SENTINEL)
#
#         pump_thread = threading.Thread(target=_pump, daemon=True)
#         pump_thread.start()
#
#         try:
#             while not stop_event.is_set():
#                 try:
#                     item = q.get(timeout=poll_timeout)
#                 except queue.Empty:
#                     continue                     # check stop_event, loop again
#
#                 if item is _SENTINEL:
#                     return
#                 if isinstance(item, Exception):
#                     raise item
#                 yield item
#         finally:
#             self.disconnect()                   # unblock the blocking read()
#             pump_thread.join(timeout=poll_timeout * 2)

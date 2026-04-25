from erie.reader.base import Reader
from erie.schema.type import ScannerTypeEnum
from typing import Iterator, Optional
from io import IOBase

# import sys
import os
import logging
import dataclasses
import select

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FileStreamReader(Reader):
    """Yields lines from stdin as a continuous generator."""

    path: str
    io: Optional[IOBase] = None
    strip: bool = True
    poll_timeout = 10

    @property
    def type(self):
        return ScannerTypeEnum.STDIN

    def present(self) -> bool:
        return os.path.exists(self.path)

    def connected(self) -> bool:
        return self.io is not None and not self.io.closed

    def read(self) -> str | None:
        """"""
        ready, _, _ = select.select([self.io], [], [], self.poll_timeout)

        if not ready:
            # Timeout: no data yet. Loop back to re-check the guards.
            return None

        try:
            line = self.io.readline()
        except ValueError:
            # stdin was closed between select() and readline().
            return None

        if not line:
            # readline() returns '' on EOF
            logger.debug("[%s] stdin EOF", self.type)
            return None

        return str(line.strip("\n"))

    def connect(self):
        logger.debug(f"[{self.__class__.__name__}] Opening '{self.path}'")
        if self.present():
            self.io = open(self.path)

    def disconnect(self) -> None:
        """Close stdin so the poll loop in stream() sees sys.stdin.closed.

        Safe to call from any thread.  Idempotent.
        """
        try:
            if self.connected():
                self.io.close()
                logger.debug(f"[{self.__class__.__name__}] Closing '{self.path}'.")
            else:
                logger.debug(f"[{self.__class__.__name__}] '{self.path}' already closed.")
        except OSError:
            pass


@dataclasses.dataclass
class IoReader(FileStreamReader):
    """Yields lines from stdin as a continuous generator."""

    io: IOBase
    path: str = ""

    def present(self) -> bool:
        """Override `present` method to point to `connected`.

        If the class pass already an IOReader (ex: stdin), override the
        'present' method to not check the path as it will be empty.
        """
        logger.debug(f"[{self.__class__.__name__}] Forwarding 'present' to 'connected'.")
        return self.connected()

    def connect(self) -> None:
        """Override `connect` method of parent class.

        If the class pass already an IOReader (ex: stdin), override the
        'connect' method to not open the path as it will be empty.
        """
        logger.debug(f"[{self.__class__.__name__}] IOReader connecting.")

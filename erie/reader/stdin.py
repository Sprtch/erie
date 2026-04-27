from erie.reader.file import IoReader
import io
import sys
import dataclasses


@dataclasses.dataclass
class Stdin(IoReader):
    """Yields lines from stdin as a continuous generator."""

    io: io.IOBase = sys.stdin

"""Standard input reader for barcode scanners.

Wraps stdin as an IoReader for use in development and testing.
"""

from erie.reader.file import IoReader
import io
import sys
import dataclasses


@dataclasses.dataclass
class Stdin(IoReader):
    """Read barcode lines from standard input."""

    io: io.IOBase = sys.stdin

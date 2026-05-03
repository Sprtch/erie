from enum import IntEnum


class ScannerTypeEnum(IntEnum):
    """List the currently supported type of scanner device."""

    UNDEFINED = 0
    """Undefined scanner"""
    STDIN = 1
    """Input from stdin"""
    TEST = 2
    """Scanner used in tests"""
    SERIAL = 3
    """Serial device scanner"""
    EVDEV = 4
    """Usb device scanner"""
    HURON = 5
    """Input from the huron webapp"""
    REDIS = 6
    """Input from redis listener"""


class ScannerModeEnum(IntEnum):
    """List supported mode for scanners."""

    UNDEFINED = 0
    """Undefined mode"""
    PRINTMODE = 1
    """Print mode, scanning a barcode will print it"""
    INVENTORYMODE = 2
    """Inventory mode, scanning a barcode will add an entry to the inventory"""

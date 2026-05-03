"""Device factory: builds reader/publisher/device objects from Config.

Maps config device entries to their corresponding reader and publisher
implementations, validating required fields along the way.
"""

from erie.config.config import Config
from erie.reader.serial import SerialReader
from erie.reader.stdin import Stdin
from erie.reader.evdev import EvdevReader

from erie.publisher.redis import Redis
from erie.publisher.stdout import Stdout

from erie.device import ErieDevice


def generate_devices_from_config(config: Config):
    """Return a list of ErieDevice instances built from the given config.

    Each device entry in config.devices is mapped to a reader (by type)
    and a publisher (by type). Raises ValueError on unknown types or
    missing required fields.

    :param config: Parsed application configuration.
    :returns: List of ready-to-run ErieDevice objects.
    """
    devices = []

    for dev in config.devices:
        if dev.type == "evdev":
            if not (dev.path or dev.device_id):
                raise ValueError(f"{dev.name}: evdev requires 'path' or 'device_id'")
            reader = EvdevReader(path=dev.path, device_id=dev.device_id)

        elif dev.type == "serial":
            if not (dev.path or dev.device_id):
                raise ValueError(f"{dev.name}: serial requires 'path' or 'device_id'")
            reader = SerialReader(path=dev.path, device_id=dev.device_id)
        elif dev.type == "stdin":
            reader = Stdin()
        else:
            raise ValueError(f"{dev.name}: unknown device type '{dev.type}'")

        out = dev.publisher
        if out.type == "redis":
            if not out.channel:
                raise ValueError(f"{dev.name}: redis publisher requires 'channel'")
            publisher = Redis(host=out.host, port=out.port, channel=out.channel)
        elif out.type == "stdout":
            publisher = Stdout()
        else:
            raise ValueError(f"{dev.name}: unknown publisher type '{out.type}'")

        device = ErieDevice(
            name=dev.name,
            reader=reader,
            publisher=publisher,
        )

        devices.append(device)

    return devices

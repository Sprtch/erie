from erie.config.config import Config
from erie.reader.serial import Serial
from erie.reader.stdin import Stdin
from erie.reader.evdev import Evdev

from erie.publisher.redis import Redis
from erie.publisher.stdout import Stdout


def generate_devices_from_config(config: Config):
    """Return devices list from config object.

    >>> config = Config.from_json("/to/json/file.json")
    >>> generate_devices_from_config(config)
    """
    devices = []

    for dev in config.devices:
        if dev.type == "evdev":
            if not (dev.path or dev.device_id):
                raise ValueError(f"{dev.name}: evdev requires 'path' or 'device_id'")
            reader = Evdev(path=dev.path, device_id=dev.device_id)

        elif dev.type == "serial":
            if not (dev.path or dev.device_id):
                raise ValueError(f"{dev.name}: serial requires 'path' or 'device_id'")
            reader = Serial(path=dev.path, device_id=dev.device_id)

        elif dev.type == "stdout":
            reader = Stdin()

        else:
            raise ValueError(f"{dev.name}: unknown device type '{dev.type}'")

        output = []

        out = dev.output
        if out.type == "redis":
            if not out.channel:
                raise ValueError(f"{dev.name}: redis output requires 'channel'")
            output.append(Redis(
                host=config.redis,
                channel=out.channel
            ))

        elif out.type == "stdout":
            output.append(Stdout())

        else:
            raise ValueError(f"{dev.name}: unknown output type '{out.type}'")

        device = Device(
            name=dev.name,
            reader=reader,
            output=output
        )

        devices.append(device)

    return devices

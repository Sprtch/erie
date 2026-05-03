from typing import Any, Optional, List, Dict
import dataclasses
import json
import yaml


@dataclasses.dataclass
class ConfigDevicePublisher:
    """Configuration for a message publisher (output channel).

    Supported publisher types:
      - ``'redis'``: Publishes messages to a Redis pub/sub channel.
        Requires ``host``, ``port``, and ``channel``.
      - ``'stdout'``: Prints messages to stdout (debugging).
        No additional fields required.
    """

    type: str = "redis"
    """Publisher type ('redis', 'stdout')"""

    host: str = "localhost"
    """Host address for 'redis' publisher type"""

    port: int = 6379
    """Port for 'redis' publisher type"""

    channel: str = "erie"
    """Communication channel for 'redis' publisher type"""


@dataclasses.dataclass
class ConfigDevice:
    """Configuration for a single barcode scanner device.

    Each device must specify a ``type`` (``'serial'``, ``'evdev'``, or
    ``'stdin'``) and either a ``path`` or ``device_id`` to locate it on
    the system.

    For ``serial`` devices the path is resolved as
    ``/dev/serial/by-id/{device_id}``.

    For ``evdev`` devices the path is resolved as
    ``/dev/input/by-id/{device_id}``.

    A device may define its own ``publisher`` block; otherwise the
    top-level default publisher is used.
    """

    name: str
    """Device name"""

    type: str
    """Device type ('evdev', 'serial', 'stdin')"""

    publisher: ConfigDevicePublisher
    """Publisher channel for the device"""

    path: Optional[str] = None
    """Device 'path' for 'evdev' & 'serial' devices"""

    device_id: Optional[str] = None
    """Device 'id' for 'evdev' & 'serial' devices"""


@dataclasses.dataclass
class Config:
    """Top-level configuration for the Erie barcode scanner daemon.

    Configuration can be loaded from a YAML or JSON file, or constructed
    from a plain dict.  All settings live under the `erie` top-level key.

    Example YAML:

    ```
    erie:
        name: "erie"
        debug: false
        nodaemon: true
        logfile: "/var/log/erie.log"
        pidfile: "/var/run/erie.pid"
        publisher:
            type: "redis"
            host: "localhost"
            port: 6379
            channel: "erie"
        devices:
            - name: "scanner1"
              type: "serial"
              id: "usb-FTDI_FT232R_USB_UART_A9UXOL6H-if00-port0"
              baudrate: 9600
            - name: "scanner2"
              type: "evdev"
              id: "usb-Belon.cn_2.4G_Wireless_Device_Belon_Smart-event-kbd"
    ```

    CLI arguments (`--debug`, `--no-daemon`, `--logfile`, `--pid`)
    override the corresponding YAML values when passed via `from_dict`.
    """

    name: str = "erie"
    """Name of the application"""

    debug: bool = False
    """Use debugging logging level (default 'warn')"""

    nodaemon: bool = False
    """Do not run the application as a daemon"""

    logfile: Optional[str] = None
    """Log file location (default: stdout)"""

    pidfile: Optional[str] = None
    """Pid file location required for daemon mode (default: None)"""

    publisher: ConfigDevicePublisher = dataclasses.field(default_factory=ConfigDevicePublisher)
    """Default 'publisher' configuration. This publisher will be used if device doesn't define any publisher."""

    devices: List[ConfigDevice] = dataclasses.field(default_factory=list)
    """Device definition array"""

    @staticmethod
    def from_dict(data: Dict[str, Any], **kwargs) -> "Config":
        """Build a :class:`Config` from a nested dict (YAML/JSON decoded).

        The dict **must** have an ``erie`` top-level key.  Any ``**kwargs``
        override matching keys in the ``erie`` section, which is how CLI
        flags (``debug``, ``nodaemon``, ``logfile``, ``pidfile``) are merged.
        Each device entry inherits the default ``publisher`` block if it does
        not define its own.

        :param data: Dict as returned by ``yaml.safe_load`` or ``json.load``.
        :param kwargs: Override values (typically from ``argparse``).

        :returns: Fully-populated :class:`Config` instance.
        """
        data = data.get("erie", {})  # Retrieve the app config
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value

        default_publisher = data.get("publisher", dataclasses.asdict(ConfigDevicePublisher()))

        devices = []
        for d in data.get("devices", []):
            out_data = d.get("publisher", default_publisher)
            publisher = ConfigDevicePublisher(
                **out_data,
            )

            devices.append(
                ConfigDevice(
                    **{
                        **d,
                        "publisher": publisher,
                    }
                )
            )

        return Config(
            **{
                **data,
                "publisher": default_publisher,
                "devices": devices,
            }
        )

    @staticmethod
    def from_yaml(path: str, **kwargs) -> "Config":
        """Load configuration from a YAML file.

        :param path: Path to the YAML configuration file.
        :param kwargs: Override values forwarded to :meth:`from_dict`.
        """
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return Config.from_dict(data, **kwargs)

    @staticmethod
    def from_json(path: str, **kwargs) -> "Config":
        """Load configuration from a JSON file.

        :param path: Path to the JSON configuration file.
        :param kwargs: Override values forwarded to :meth:`from_dict`.
        """
        with open(path) as f:
            data = json.load(f)
        return Config.from_dict(data, **kwargs)

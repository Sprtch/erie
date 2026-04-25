from typing import Any, Optional, List, Dict
import dataclasses
import json
import yaml


@dataclasses.dataclass
class ConfigDevicePublisher:
    type: str
    """Publisher type ('redis', 'stdout')"""

    host: str = "localhost"
    """Host address for 'redis' publisher type"""

    port: int = 6379
    """Port for 'redis' publisher type"""

    channel: str = "erie"
    """Communication channel for 'redis' publisher type"""


@dataclasses.dataclass
class ConfigDevice:
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
    """Configuration schema."""

    name: str = "erie"
    """Name of the application"""

    redis: str = "victoria"

    debug: bool = False
    """Use debugging logging level (default 'warn')"""

    nodaemon: bool = False
    """Do not run the application as a daemon"""

    logfile: Optional[str] = None
    """Log file location (default: stdout)"""

    pidfile: Optional[str] = None
    """Pid file location required for daemon mode (default: None)"""

    devices: List[ConfigDevice] = dataclasses.field(default_factory=list)
    """Device definition array"""

    @staticmethod
    def from_dict(data: Dict[str, Any], **kwargs) -> "Config":
        data = data.get("erie", {})  # Retrieve the app config
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value

        devices = []
        for d in data.get("devices", []):
            out_data = d.get("publisher", {})
            publisher = ConfigDevicePublisher(
                type=out_data.get("type", "stdout"),
                host=out_data.get("host", "localhost"),
                port=out_data.get("port", 6379),
                channel=out_data.get("channel", "erie"),
            )

            devices.append(
                ConfigDevice(
                    name=d["name"],
                    type=d["type"],
                    publisher=publisher,
                    path=d.get("path"),
                    device_id=d.get("device_id"),
                )
            )

        return Config(
            name=data.get("name", Config.name),
            redis=data.get("redis", Config.redis),
            debug=data.get("debug", Config.debug),
            nodaemon=data.get("nodaemon", Config.nodaemon),
            logfile=data.get("logfile"),
            pidfile=data.get("pidfile"),
            devices=devices,
        )

    @staticmethod
    def from_yaml(path: str, **kwargs) -> "Config":
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return Config.from_dict(data, **kwargs)

    @staticmethod
    def from_json(path: str, **kwargs) -> "Config":
        with open(path) as f:
            data = json.load(f)
        return Config.from_dict(data, **kwargs)

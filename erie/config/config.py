from typing import Any, Optional, List, Dict
import dataclasses
import json
import yaml


@dataclasses.dataclass
class ConfigDevicePublisher:
    """Publisher configuration."""

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
    """Device configuration."""

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
                ConfigDevice(**{
                    **d,
                    "publisher": publisher,
                })
            )

        return Config(**{
            **data,
            "publisher": default_publisher,
            "devices": devices,
        })

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

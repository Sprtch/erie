from typing import Any, Optional, List, Dict
import dataclasses
import json
import yaml


@dataclasses.dataclass
class ConfigDeviceOutput:
    type: str
    """Output type ('redis', 'stdout')"""

    host: Optional[str] = None
    """Host address for 'redis' output type"""

    channel: Optional[str] = None
    """Communication channel for 'redis' output type"""


@dataclasses.dataclass
class ConfigDevice:
    name: str
    """Device name"""

    type: str
    """Device type ('evdev', 'serial', 'stdin')"""

    output: ConfigDeviceOutput
    """Output channel for the device"""

    path: Optional[str] = None
    """Device 'path' for 'evdev' & 'serial' devices"""

    device_id: Optional[str] = None
    """Device 'id' for 'evdev' & 'serial' devices"""

@dataclasses.dataclass
class Config:
    name: str = "erie"
    redis: str = "victoria"
    debug: bool = False
    nodaemon: bool = False
    logfile: Optional[str] = None
    pidfile: Optional[str] = None
    devices: List[ConfigDevice] = dataclasses.field(default_factory=list)

    @staticmethod
    def from_dict(data: Dict[str, Any], **kwargs) -> "Config":
        data = dict(data)  # copy
        data.update(kwargs)

        devices = []
        for d in data.get("devices", []):
            output = ConfigDeviceOutput(d.get("outputs", {}))

            devices.append(ConfigDevice(
                name=d["name"],
                type=d["type"],
                output=output,
            ))

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

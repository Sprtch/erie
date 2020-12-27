from erie.devices.inputdevice import InputDeviceWrapper
from erie.devices.serialdevice import SerialWrapper
from erie.devices.stdindevice import StdinWrapper
from erie.db import init_db, db
import dataclasses
import os
import yaml


class InvalidConfigFile(Exception):
    pass


@dataclasses.dataclass
class DbConfig:
    uri: str = 'sqlite://'


@dataclasses.dataclass
class Config:
    APPNAME = "erie"
    redis: str = "victoria"
    devices: list = dataclasses.field(default_factory=list)
    debug: bool = False
    logfile: str = ""
    pidfile: str = ""
    nodaemon: bool = False

    def __post_init__(self):
        devices = []
        for dev in self.devices:
            name, content = list(dev.items())[0]
            args = {
                'name': name,
                'path': content.get('path'),
                'deviceid': content.get('id'),
                'redis': content.get('redis', self.redis)
            }
            devicetype = content.get('type')
            if devicetype == 'evdev':
                devices.append(InputDeviceWrapper(**args))
            elif devicetype == 'serial':
                devices.append(SerialWrapper(**args))
            elif devicetype == 'stdin':
                devices.append(StdinWrapper(**args))
            else:
                raise InvalidConfigFile("Type not supported")

        if self.debug and not len(
                list(
                    filter(lambda x: isinstance(x, StdinWrapper),
                           self.devices))):
            devices.append(StdinWrapper(name="STDIN", redis=self.redis))

        self.devices = devices

    @staticmethod
    def from_dict(raw, **kwargs):
        erie_args = {**kwargs, **raw['erie']}
        raw['erie'] = erie_args
        if raw.get('despinassy') is not None:
            dbconfig = DbConfig(**raw['despinassy'])
            init_db(dbconfig)
        else:
            dbconfig = DbConfig()
            init_db(dbconfig)
            db.create_all()

        if raw.get(Config.APPNAME) is not None:
            config = raw[Config.APPNAME]
        else:
            raise InvalidConfigFile("No '%s' field in the config file." %
                                    (Config.APPNAME))

        return Config(**config)

    @staticmethod
    def from_yaml_file(filename, **kwargs):
        if os.path.isfile(filename):
            raw = yaml.load(open(filename, 'r'), Loader=yaml.FullLoader)
        else:
            raise InvalidConfigFile('No config file in "%s"' % (filename))

        return Config.from_dict(raw, **kwargs)

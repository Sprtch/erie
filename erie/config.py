from erie.devices.inputdevice import InputDeviceWrapper
from erie.devices.serialdevice import SerialWrapper
from erie.devices.stdindevice import StdinWrapper
from erie.logger import init_log
from typing import Optional
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
    logfile: Optional[str] = None
    pidfile: Optional[str] = None
    nodaemon: bool = False
    database: DbConfig = DbConfig()

    def __post_init__(self):
        init_log(self)
        devices = []
        for dev in self.devices:
            name, content = list(dev.items())[0]
            devicetype = content.get('type')
            if devicetype == 'evdev':
                args = {
                    'name': name,
                    'path': content.get('path'),
                    'deviceid': content.get('id'),
                    'redis': content.get('redis', self.redis)
                }
                devices.append(InputDeviceWrapper(**args))
            elif devicetype == 'serial':
                args = {
                    'name': name,
                    'path': content.get('path'),
                    'deviceid': content.get('id'),
                    'redis': content.get('redis', self.redis)
                }
                devices.append(SerialWrapper(**args))
            elif devicetype == 'stdin':
                args = {
                    'name': name,
                    'redis': content.get('redis', self.redis)
                }
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
        config = {}
        raw[Config.APPNAME] = {**kwargs, **raw[Config.APPNAME]}

        # if raw.get('despinassy') is not None:
        #     dbconfig = DbConfig(**raw['despinassy'])
        #     init_db(dbconfig)
        # else:
        #     dbconfig = DbConfig()
        #     init_db(dbconfig)
        #     db.create_all()

        if raw.get(Config.APPNAME) is not None:
            config = raw[Config.APPNAME]
        else:
            raise InvalidConfigFile("No '%s' field in the config file." %
                                    (Config.APPNAME))

        if raw.get('despinassy') is not None:
            config['database'] = DbConfig(**raw['despinassy'])

        return Config(**config)

    @staticmethod
    def from_yaml_file(filename, **kwargs):
        if os.path.isfile(filename):
            raw = yaml.load(open(filename, 'r'), Loader=yaml.FullLoader)
        else:
            raise InvalidConfigFile('No config file in "%s"' % (filename))

        return Config.from_dict(raw, **kwargs)

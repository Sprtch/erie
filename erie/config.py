from erie.devices.inputdevice import InputDeviceWrapper
from erie.devices.serialdevice import SerialWrapper
from erie.devices.stdindevice import StdinWrapper
from erie.logger import logger
import os
import yaml


class InvalidConfigFile(Exception):
    pass


class Config:
    REDIS_DEFAULT_CHAN = "victoria"

    def __init__(self, configpath, debug=False):
        self.devices = []
        self.db = None
        if os.path.isfile(configpath):
            raw = yaml.load(open(configpath, 'r'), Loader=yaml.FullLoader)
        else:
            raise InvalidConfigFile('No config file in "%s"' % (configpath))

        self.db = raw.get('despinassy', {})

        if raw.get('erie') is not None:
            config = raw['erie']
        else:
            raise InvalidConfigFile("No 'erie' field in the config file.")

        redis_default = config.get('redis', Config.REDIS_DEFAULT_CHAN)

        devices = config.get('devices', [])

        for dev in devices:
            name, content = list(dev.items())[0]
            args = {
                'name': name,
                'path': content.get('path'),
                'deviceid': content.get('id'),
                'redis': content.get('redis', redis_default)
            }
            devicetype = content.get('type')
            if devicetype == 'evdev':
                self.devices.append(InputDeviceWrapper(**args))
            elif devicetype == 'serial':
                self.devices.append(SerialWrapper(**args))
            elif devicetype == 'stdin':
                self.devices.append(StdinWrapper(**args))
            else:
                raise InvalidConfigFile("Type not supported")

        if debug and not len(
                list(
                    filter(lambda x: isinstance(x, StdinWrapper),
                           self.devices))):
            self.devices.append(StdinWrapper(name="STDIN",
                                             redis=redis_default))

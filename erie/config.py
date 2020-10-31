from erie.devices.inputdevice import InputDeviceWrapper
from erie.devices.serialdevice import SerialWrapper
from erie.logger import logger
import os
import yaml

class InvalidConfigFile(Exception):
    pass

class Config:
    REDIS_DEFAULT_CHAN = "victoria"

    def __init__(self, configpath):
        self.devices = []
        if os.path.isfile(configpath):
            raw = yaml.load(open(configpath, 'r'), Loader=yaml.FullLoader)
        else:
            pass # TODO Load default config

        if raw.get('erie') is not None:
            config = raw['erie']
        else:
            raise InvalidConfigFile("No 'erie' field in the config file.")
        
        redis_default = config.get('redis', Config.REDIS_DEFAULT_CHAN)

        devices = config.get('devices', [])
        # if type(devices) != list:
        #     logger.error("")
        #     raise InvalidConfigFile("Invalid configuration provided")

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
            else:
                raise InvalidConfigFile("Type not supported")

from erie.devices.inputdevice import InputDeviceWrapper
from erie.devices.serialdevice import SerialWrapper
import os
import yaml

class Config:
    def __init__(self, path):
        pass
        raw = yaml.load(open(args.config, 'r'), Loader=yaml.FullLoader)


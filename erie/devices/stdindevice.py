from erie.devices.device import DeviceWrapper

class StdinWrapper(DeviceWrapper):
    def __init__(self, name, redis, **kwargs):
        super().__init__("STDIN", name, redis)

    def present(self):
        return True

    def retrieve(self):
        while 1:
            line = input()
            if line:
                yield line

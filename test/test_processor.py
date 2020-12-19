import unittest
from despinassy.ipc import create_nametuple
from erie.message import Message
from erie.devices.stdindevice import StdinWrapper
from erie.devices.device import DeviceWrapper
from erie.processor import Processor

class DeviceTester(DeviceWrapper):
    def __init__(self, input_list=[]):
        super().__init__("TEST", "test", "test")
        self.input_list = input_list

    def retrieve(self):
        for msg in self.input_list:
            yield msg

    def read_loop(self):
        for x in self.retrieve():
            yield create_nametuple(Message, {}, barcode=x, device=self._device_type, name=self.name, redis=self.redis)

class ProcessorTester(Processor):
    def __init__(self, dev):
        super().__init__(dev)
        self._msgs = []

    def process(self, msg):
        self._msgs.append(self._process_pipe(msg))
        self._reset_process_pipe()

    def clear(self):
        self._msgs = []

    def get_messages(self):
        return self._msgs

class TestProcessor(unittest.TestCase):
    def test_processor_none(self):
        dev = DeviceTester()
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [])

    def test_processor_barcode(self):
        RESULT = Message(barcode='FOO1234BAR', device='TEST', redis='test', name='test', number=1)
        dev = DeviceTester(["FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

    def test_proessor_multiplier(self):
        RESULT = Message(barcode='FOO1234BAR', device='TEST', redis='test', name='test', number=2)
        dev = DeviceTester(["SPRTCHCMD:MULTIPLIER:2", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

        RESULT = Message(barcode='FOO1234BAR', device='TEST', redis='test', name='test', number=4)
        dev = DeviceTester(["SPRTCHCMD:MULTIPLIER:4", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

        RESULT = Message(barcode='FOO1234BAR', device='TEST', redis='test', name='test', number=8)
        dev = DeviceTester(["SPRTCHCMD:MULTIPLIER:4", "SPRTCHCMD:MULTIPLIER:2", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

    def test_processor_clear(self):
        RESULT = Message(barcode='FOO1234BAR', device='TEST', redis='test', name='test', number=1)
        dev = DeviceTester(["SPRTCHCMD:MULTIPLIER:4", "SPRTCHCMD:MULTIPLIER:2", "SPRTCHCMD:CLEAR:0", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

    def test_processor_negative(self):
        RESULT = Message(barcode='FOO1234BAR', device='TEST', redis='test', name='test', number=-4)
        dev = DeviceTester(["SPRTCHCMD:MULTIPLIER:4", "SPRTCHCMD:NEGATIVE:0", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])
        dev = DeviceTester(["SPRTCHCMD:NEGATIVE:0", "SPRTCHCMD:MULTIPLIER:4", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()

if __name__ == '__main__':
    unittest.main()

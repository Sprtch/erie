import unittest
from despinassy.Scanner import ScannerTypeEnum
from despinassy.ipc import create_nametuple
from erie.message import Message
from erie.devices.device import DeviceWrapper
from erie.processor import Processor
import dataclasses


@dataclasses.dataclass
class DeviceTester(DeviceWrapper):
    DEVICE_TYPE: ScannerTypeEnum = ScannerTypeEnum.TEST
    input_list: list = dataclasses.field(default_factory=list)

    def retrieve(self):
        for msg in self.input_list:
            yield msg

    def read_loop(self):
        for x in self.retrieve():
            yield create_nametuple(Message, {},
                                   barcode=x,
                                   device=str(self.DEVICE_TYPE),
                                   name=self.name,
                                   redis=self.redis)


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
        dev = DeviceTester(
            name="test",
            redis="test",
        )
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [])

    def test_processor_barcode(self):
        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=1)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=["FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

    def test_proessor_multiplier(self):
        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=2)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=["SPRTCHCMD:MULTIPLIER:2", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=4)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=["SPRTCHCMD:MULTIPLIER:4", "FOO1234BAR"])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=8)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:MULTIPLIER:4",
                               "SPRTCHCMD:MULTIPLIER:2", "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

    def test_processor_clear(self):
        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=1)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:MULTIPLIER:4",
                               "SPRTCHCMD:MULTIPLIER:2", "SPRTCHCMD:CLEAR:0",
                               "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

    def test_processor_negative(self):
        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=-4)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:MULTIPLIER:4",
                               "SPRTCHCMD:NEGATIVE:0", "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:NEGATIVE:0",
                               "SPRTCHCMD:MULTIPLIER:4", "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()

    def test_processor_digit(self):
        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=42.0)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DIGIT:4", "SPRTCHCMD:DIGIT:2",
                               "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DIGIT:0", "SPRTCHCMD:DIGIT:4",
                               "SPRTCHCMD:DIGIT:2", "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        msgs = proc.get_messages()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].number, 42)

        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DIGIT:0", "SPRTCHCMD:DIGIT:4",
                               "SPRTCHCMD:DIGIT:2", "SPRTCHCMD:MULTIPLIER:2",
                               "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        msgs = proc.get_messages()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].number, 84)

        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DIGIT:0", "SPRTCHCMD:DIGIT:4",
                               "SPRTCHCMD:MULTIPLIER:2", "SPRTCHCMD:DIGIT:2",
                               "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        msgs = proc.get_messages()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].number, 82)

    def test_processor_dotted(self):
        RESULT = Message(barcode='FOO1234BAR',
                         device='ScannerTypeEnum.TEST',
                         redis='test',
                         name='test',
                         number=4.2)
        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DIGIT:4", "SPRTCHCMD:DOTTED:0",
                               "SPRTCHCMD:DIGIT:2", "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        self.assertEqual(proc.get_messages(), [RESULT])

        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DOTTED:0", "SPRTCHCMD:DIGIT:2",
                               "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        msgs = proc.get_messages()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].number, .2)

        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DOTTED:0", "SPRTCHCMD:DIGIT:2",
                               "SPRTCHCMD:MULTIPLIER:2", "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        msgs = proc.get_messages()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].number, .4)

        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DOTTED:0", "SPRTCHCMD:DIGIT:2",
                               "SPRTCHCMD:MULTIPLIER:2", "SPRTCHCMD:DIGIT:2",
                               "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        msgs = proc.get_messages()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].number, .42)

        dev = DeviceTester(name="test",
                           redis="test",
                           input_list=[
                               "SPRTCHCMD:DOTTED:0", "SPRTCHCMD:DIGIT:2",
                               "SPRTCHCMD:MULTIPLIER:2", "SPRTCHCMD:DIGIT:2",
                               "SPRTCHCMD:NEGATIVE:0", "FOO1234BAR"
                           ])
        proc = ProcessorTester(dev)
        proc.read()
        msgs = proc.get_messages()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].number, -0.42)


if __name__ == '__main__':
    unittest.main()

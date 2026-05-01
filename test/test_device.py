import unittest
import unittest.mock
import threading
import io
import sys
from erie.device import ErieDevice
from erie.reader.base import Reader
from erie.reader.stdin import Stdin
from erie.reader.file import FileStreamReader
from erie.publisher.base import Publisher
from erie.processor.base import Processor
from erie.schema.type import ScannerTypeEnum


class MockPublisher(Publisher):
    def __init__(self):
        self.sent = []

    def available(self):
        return True

    def send(self, msg):
        self.sent.append(msg)


class MockReader(Reader):
    def __init__(self, present_result=True, read_values=None):
        self._present_result = present_result
        self._read_values = read_values or []
        self._read_idx = 0
        self._type = ScannerTypeEnum.STDIN

    @property
    def type(self):
        return self._type

    def present(self):
        return self._present_result

    def read(self):
        if self._read_idx < len(self._read_values):
            val = self._read_values[self._read_idx]
            self._read_idx += 1
            return val
        return None


class TestErieDevice(unittest.TestCase):
    def test_device_initialization(self):
        reader = MockReader()
        publisher = MockPublisher()
        device = ErieDevice(name="test", reader=reader, publisher=publisher)

        self.assertEqual(device.name, "test")
        self.assertIs(device.reader, reader)
        self.assertIs(device.publisher, publisher)
        self.assertIsInstance(device.processor, Processor)

    def test_device_initialization_with_custom_processor(self):
        reader = MockReader()
        publisher = MockPublisher()
        processor = Processor()
        device = ErieDevice(name="test", reader=reader, publisher=publisher, processor=processor)

        self.assertIs(device.processor, processor)

    def test_read_loop_stops_on_event(self):
        reader = MockReader(present_result=True, read_values=["data1", "data2"])
        publisher = MockPublisher()
        device = ErieDevice(name="test", reader=reader, publisher=publisher)

        stop_event = threading.Event()
        stop_event.set()

        device.read_loop(stop_event=stop_event)

    def test_read_loop_exits_when_not_present(self):
        reader = MockReader(present_result=False)
        publisher = MockPublisher()
        device = ErieDevice(name="test", reader=reader, publisher=publisher)

        stop_event = threading.Event()
        stop_event.set()

        device.read_loop(stop_event=stop_event)

    def test_read_loop_yields_content(self):
        reader = MockReader(present_result=True, read_values=["test"])
        publisher = MockPublisher()
        device = ErieDevice(name="test", reader=reader, publisher=publisher)

        stop_event = threading.Event()

        thread = threading.Thread(target=device.read_loop, args=(stop_event,))
        thread.start()

        stop_event.set()
        thread.join(timeout=2)

    def test_disconnect(self):
        reader = MockReader()
        publisher = MockPublisher()
        device = ErieDevice(name="test", reader=reader, publisher=publisher)

        device.disconnect()


class TestStdinReader(unittest.TestCase):
    def test_stdin_present(self):
        stdin = Stdin()
        self.assertTrue(stdin.present())

    def test_stdin_context_manager(self):
        stdin = Stdin()
        with stdin:
            self.assertTrue(stdin.present())

    def test_file_stream_reader_connected_false_when_closed(self):
        mock_file = io.StringIO()
        reader = FileStreamReader(io=mock_file, path="/dev/null")
        self.assertTrue(reader.connected())

        mock_file.close()
        self.assertFalse(reader.connected())


if __name__ == "__main__":
    unittest.main()

import io
import logging
import threading
import unittest
import unittest.mock
import threading
import io
import logging
from erie.reader.base import Reader
from erie.reader.stdin import Stdin
from erie.reader.file import FileStreamReader
from erie.reader.serial import SerialReader, SerialWrapper
from erie.reader.evdev import EvdevReader, EvdevWrapper
from erie.reader.redis import RedisReader
from erie.schema.type import ScannerTypeEnum

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockPublisher:
    def __init__(self):
        self.sent = []

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


class TestReaderBase(unittest.TestCase):
    def test_reader_abstract_methods(self):
        with self.assertRaises(TypeError):
            Reader()

    def test_reader_retrieve_respects_stop_event(self):
        class TestReader(Reader):
            @property
            def type(self):
                return ScannerTypeEnum.STDIN

            def present(self):
                return True

            def read(self):
                return None

        reader = TestReader()
        stop_event = threading.Event()
        stop_event.set()

        results = list(reader.retrieve(stop_event))
        self.assertEqual(results, [])

    def test_reader_retrieve_yields_content(self):
        results = []

        class TestReader(Reader):
            @property
            def type(self):
                return ScannerTypeEnum.STDIN

            def present(self):
                return len(results) < 1

            def read(self):
                results.append("test")
                return "test\n"

        reader = TestReader()
        stop_event = threading.Event()

        result = list(reader.retrieve(stop_event, poll_timeout=0.05))
        self.assertEqual(result, ["test"])

    def test_reader_context_manager(self):
        connected = False

        class TestReader(Reader):
            @property
            def type(self):
                return ScannerTypeEnum.STDIN

            def present(self):
                return connected

            def read(self):
                return None

            def connect(self):
                nonlocal connected
                connected = True

            def disconnect(self):
                nonlocal connected
                connected = False

        reader = TestReader()
        self.assertFalse(connected)

        with reader:
            self.assertTrue(connected)

        self.assertFalse(connected)


class TestFileStreamReader(unittest.TestCase):
    def test_present_true_when_file_exists(self):
        reader = FileStreamReader(io=None, path="/dev/null")
        self.assertTrue(reader.present())

    def test_present_false_when_file_missing(self):
        reader = FileStreamReader(io=None, path="/nonexistent")
        self.assertFalse(reader.present())

    def test_connected_true_when_io_open(self):
        mock_file = io.StringIO()
        reader = FileStreamReader(io=mock_file, path="/dev/null")
        self.assertTrue(reader.connected())

    def test_connected_false_when_io_closed(self):
        mock_file = io.StringIO()
        reader = FileStreamReader(io=mock_file, path="/dev/null")
        mock_file.close()
        self.assertFalse(reader.connected())

    def test_context_manager(self):
        mock_file = io.StringIO()
        reader = FileStreamReader(io=mock_file, path="/dev/null")

        with reader:
            self.assertTrue(reader.connected())

        self.assertFalse(reader.connected())


class TestStdinReader(unittest.TestCase):
    def test_stdin_present(self):
        stdin = Stdin()
        self.assertTrue(stdin.present())

    def test_stdin_context_manager(self):
        stdin = Stdin()
        with stdin:
            self.assertTrue(stdin.present())


class TestSerialReader(unittest.TestCase):
    def test_serial_present_false_when_file_missing(self):
        reader = SerialReader(path="/nonexistent")
        self.assertFalse(reader.present())

    def test_serial_present_true_when_device_exists(self):
        with unittest.mock.patch("os.path.exists", return_value=True):
            reader = SerialReader(path="/dev/serial/by-id/test-device")
            self.assertTrue(reader.present())

    def test_serial_connected_false_when_io_closed(self):
        mock_dev = unittest.mock.MagicMock()
        mock_dev.is_open = False
        wrapper = SerialWrapper(mock_dev)
        self.assertTrue(wrapper.closed)

    def test_serial_connected_true_when_io_open(self):
        mock_dev = unittest.mock.MagicMock()
        mock_dev.is_open = True
        wrapper = SerialWrapper(mock_dev)
        self.assertFalse(wrapper.closed)

    def test_serial_context_manager(self):
        with unittest.mock.patch("os.path.exists", return_value=True):
            with unittest.mock.patch("serial.Serial") as mock_serial_class:
                mock_serial = unittest.mock.MagicMock()
                mock_serial.is_open = True
                mock_serial_class.return_value = mock_serial

                reader = SerialReader(device_id="test-device")
                with reader:
                    self.assertIsNotNone(reader.io)
                    self.assertFalse(reader.io.closed)

                mock_serial.close.assert_called_once()

    def test_serial_readline_returns_stripped_string(self):
        mock_dev = unittest.mock.MagicMock()
        mock_dev.readline.return_value = b"test-barcode\n"
        wrapper = SerialWrapper(mock_dev)
        self.assertEqual(wrapper.readline(), "test-barcode")

    def test_serial_readline_returns_empty_on_no_data(self):
        mock_dev = unittest.mock.MagicMock()
        mock_dev.readline.return_value = b""
        wrapper = SerialWrapper(mock_dev)
        self.assertEqual(wrapper.readline(), "")


class TestRedisReader(unittest.TestCase):
    def _make_reader(self, **kwargs):
        defaults = {"channel": "test-channel", "host": "localhost", "port": 6379, "db": 0}
        defaults.update(kwargs)
        return RedisReader(**defaults)

    def test_present_true_when_ping_succeeds(self):
        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_client.ping.return_value = True
            mock_redis_cls.return_value = mock_client

            self.assertTrue(reader.present())

    def test_present_false_when_ping_fails(self):
        import redis as redis_lib

        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_client.ping.side_effect = redis_lib.RedisError("connection refused")
            mock_redis_cls.return_value = mock_client

            self.assertFalse(reader.present())

    def test_present_resets_client_on_failure(self):
        import redis as redis_lib

        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_client.ping.side_effect = redis_lib.RedisError("down")
            mock_redis_cls.return_value = mock_client

            reader.present()
            self.assertIsNone(reader._client)
            self.assertIsNone(reader._pubsub)

    def test_client_lazy_initialization(self):
        reader = self._make_reader()
        self.assertIsNone(reader._client)
        self.assertIsNone(reader._pubsub)

        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            mock_redis_cls.assert_called_once_with(
                host="localhost", port=6379, db=0, decode_responses=True
            )
            mock_client.pubsub.assert_called_once()
            self.assertIs(reader._client, mock_client)

    def test_client_reuses_existing_instance(self):
        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_redis_cls.return_value = mock_client

            first = reader.client
            second = reader.client
            self.assertIs(first, second)
            mock_redis_cls.assert_called_once()

    def test_connect_subscribes_to_channel(self):
        reader = self._make_reader(channel="my-channel")
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_pubsub = unittest.mock.MagicMock()
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            reader.connect()
            mock_pubsub.subscribe.assert_called_once_with("my-channel")

    def test_disconnect_unsubscribes_from_channel(self):
        reader = self._make_reader(channel="my-channel")
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_pubsub = unittest.mock.MagicMock()
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            reader.connect()
            reader.disconnect()
            mock_pubsub.unsubscribe.assert_called_once_with("my-channel")

    def test_read_returns_data_on_message(self):
        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_pubsub = unittest.mock.MagicMock()
            mock_pubsub.get_message.return_value = {
                "type": "message",
                "data": "barcode-123",
            }
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            reader.connect()
            self.assertEqual(reader.read(), "barcode-123")

    def test_read_returns_data_on_pmessage(self):
        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_pubsub = unittest.mock.MagicMock()
            mock_pubsub.get_message.return_value = {
                "type": "pmessage",
                "data": "barcode-456",
            }
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            reader.connect()
            self.assertEqual(reader.read(), "barcode-456")

    def test_read_returns_none_when_no_message(self):
        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_pubsub = unittest.mock.MagicMock()
            mock_pubsub.get_message.return_value = None
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            reader.connect()
            self.assertIsNone(reader.read())

    def test_read_returns_none_on_subscribe_confirmation(self):
        reader = self._make_reader()
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_pubsub = unittest.mock.MagicMock()
            mock_pubsub.get_message.return_value = {
                "type": "subscribe",
                "channel": "test-channel",
            }
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            reader.connect()
            self.assertIsNone(reader.read())

    def test_context_manager_connects_and_disconnects(self):
        reader = self._make_reader(channel="ctx-channel")
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_pubsub = unittest.mock.MagicMock()
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            with reader:
                mock_pubsub.subscribe.assert_called_once_with("ctx-channel")

            mock_pubsub.unsubscribe.assert_called_once_with("ctx-channel")

    def test_custom_connection_params(self):
        reader = self._make_reader(host="10.0.0.1", port=6380, db=3)
        with unittest.mock.patch("redis.Redis") as mock_redis_cls:
            mock_client = unittest.mock.MagicMock()
            mock_redis_cls.return_value = mock_client

            _ = reader.client
            mock_redis_cls.assert_called_once_with(
                host="10.0.0.1", port=6380, db=3, decode_responses=True
            )


class TestMockReader(unittest.TestCase):
    def test_mock_reader_basic(self):
        reader = MockReader(present_result=True, read_values=["a", "b"])
        self.assertTrue(reader.present())

        self.assertEqual(reader.read(), "a")
        self.assertEqual(reader.read(), "b")
        self.assertIsNone(reader.read())

    def test_mock_reader_not_present(self):
        reader = MockReader(present_result=False)
        self.assertFalse(reader.present())

    def test_mock_reader_with_newline(self):
        reader = MockReader(present_result=True, read_values=["test\n", "data\n"])
        self.assertEqual(reader.read(), "test\n")
        self.assertEqual(reader.read(), "data\n")

    def test_mock_reader_empty(self):
        reader = MockReader(present_result=True, read_values=[])
        self.assertIsNone(reader.read())
        self.assertIsNone(reader.read())


if __name__ == "__main__":
    unittest.main()

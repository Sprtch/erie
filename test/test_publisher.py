import io
import json
import sys
import unittest
import unittest.mock

from erie.publisher.base import Publisher
from erie.publisher.redis import Redis
from erie.publisher.stdout import Stdout
from erie.schema.message import IpcInventoryMessage, IpcPrintMessage


class TestPublisherBase(unittest.TestCase):
    def test_publisher_is_abstract(self):
        with self.assertRaises(TypeError):
            Publisher()

    def test_publisher_subclass_must_implement_send(self):
        class MinimalPublisher(Publisher):
            def send(self, msg):
                return msg

        pub = MinimalPublisher()
        self.assertIsInstance(pub, Publisher)


class TestRedisPublisher(unittest.TestCase):
    def test_redis_initialization_defaults(self):
        pub = Redis()
        self.assertEqual(pub.host, "localhost")
        self.assertEqual(pub.channel, "erie")
        self.assertEqual(pub.port, 6379)
        self.assertEqual(pub.db, 0)
        self.assertIsNone(pub._client)

    def test_redis_initialization_custom(self):
        pub = Redis(host="redis.example.com", channel="test", port=6380, db=1)
        self.assertEqual(pub.host, "redis.example.com")
        self.assertEqual(pub.channel, "test")
        self.assertEqual(pub.port, 6380)
        self.assertEqual(pub.db, 1)

    @unittest.mock.patch("erie.publisher.redis.redis.Redis")
    def test_send_with_ipc_message(self, mock_redis_class):
        mock_client = unittest.mock.MagicMock()
        mock_redis_class.return_value = mock_client

        pub = Redis()
        msg = IpcPrintMessage(device="scanner1", content="123456")
        pub.send(msg)

        mock_client.publish.assert_called_once()
        args = mock_client.publish.call_args[0]
        self.assertEqual(args[0], "erie")
        payload = json.loads(args[1])
        self.assertEqual(payload["device"], "scanner1")
        self.assertEqual(payload["content"], "123456")

    @unittest.mock.patch("erie.publisher.redis.redis.Redis")
    def test_send_with_inventory_message(self, mock_redis_class):
        mock_client = unittest.mock.MagicMock()
        mock_redis_class.return_value = mock_client

        pub = Redis(channel="inventory")
        msg = IpcInventoryMessage(device="scanner2", action=2)
        pub.send(msg)

        mock_client.publish.assert_called_once()
        args = mock_client.publish.call_args[0]
        self.assertEqual(args[0], "inventory")

    @unittest.mock.patch("erie.publisher.redis.redis.Redis")
    def test_send_with_object_having_dict(self, mock_redis_class):
        mock_client = unittest.mock.MagicMock()
        mock_redis_class.return_value = mock_client

        pub = Redis()
        msg = unittest.mock.MagicMock()
        msg.__dict__ = {"foo": "bar"}

        pub.send(msg)

        mock_client.publish.assert_called_once()
        args = mock_client.publish.call_args[0]
        payload = json.loads(args[1])
        self.assertEqual(payload, {"foo": "bar"})

    @unittest.mock.patch("erie.publisher.redis.redis.Redis")
    def test_send_with_plain_string(self, mock_redis_class):
        mock_client = unittest.mock.MagicMock()
        mock_redis_class.return_value = mock_client

        pub = Redis()
        pub.send("plain string")

        mock_client.publish.assert_called_once()
        args = mock_client.publish.call_args[0]
        self.assertEqual(args[1], "plain string")

    @unittest.mock.patch("erie.publisher.redis.redis.Redis")
    def test_send_redis_error_propagates(self, mock_redis_class):
        import redis

        mock_client = unittest.mock.MagicMock()
        mock_client.publish.side_effect = redis.RedisError("connection failed")
        mock_redis_class.return_value = mock_client

        pub = Redis()
        msg = IpcPrintMessage(device="scanner1", content="123456")

        with self.assertRaises(redis.RedisError):
            pub.send(msg)


class TestStdoutPublisher(unittest.TestCase):
    def test_stdout_send(self):
        pub = Stdout()
        msg = IpcPrintMessage(device="scanner1", content="123456")

        captured = io.StringIO()
        sys.stdout = captured
        try:
            pub.send(msg)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        payload = json.loads(output)
        self.assertEqual(payload["device"], "scanner1")
        self.assertEqual(payload["content"], "123456")

    def test_stdout_send_inventory(self):
        pub = Stdout()
        msg = IpcInventoryMessage(device="scanner2", action=1)

        captured = io.StringIO()
        sys.stdout = captured
        try:
            pub.send(msg)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        payload = json.loads(output)
        self.assertEqual(payload["device"], "scanner2")
        self.assertEqual(payload["action"], 1)


if __name__ == "__main__":
    unittest.main()

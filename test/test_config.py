import unittest
import tempfile
import os
from erie.config.config import Config, ConfigDevice, ConfigDevicePublisher


class TestConfig(unittest.TestCase):
    def test_config_from_dict_minimal(self):
        config_dict = {"erie": {}}
        conf = Config.from_dict(config_dict)

        self.assertEqual(conf.name, "erie")
        self.assertFalse(conf.debug)
        self.assertEqual(conf.devices, [])

    def test_config_from_dict_full(self):
        config_dict = {
            "erie": {
                "name": "testapp",
                "debug": True,
                "nodaemon": True,
                "logfile": "/var/log/erie.log",
                "pidfile": "/var/run/erie.pid",
                "devices": [
                    {
                        "name": "scanner1",
                        "type": "stdin",
                        "publisher": {
                            "type": "redis",
                            "host": "localhost",
                            "channel": "erie_events",
                        },
                    },
                    {
                        "name": "scanner2",
                        "type": "evdev",
                        "path": "/dev/input/event0",
                        "publisher": {
                            "type": "stdout",
                        },
                    },
                ],
            }
        }

        conf = Config.from_dict(config_dict)

        self.assertEqual(conf.name, "testapp")
        self.assertTrue(conf.debug)
        self.assertTrue(conf.nodaemon)
        self.assertEqual(conf.logfile, "/var/log/erie.log")
        self.assertEqual(conf.pidfile, "/var/run/erie.pid")
        self.assertEqual(len(conf.devices), 2)

        device1 = conf.devices[0]
        self.assertIsInstance(device1, ConfigDevice)
        self.assertEqual(device1.name, "scanner1")
        self.assertEqual(device1.type, "stdin")
        self.assertIsInstance(device1.publisher, ConfigDevicePublisher)
        self.assertEqual(device1.publisher.type, "redis")
        self.assertEqual(device1.publisher.host, "localhost")
        self.assertEqual(device1.publisher.channel, "erie_events")
        self.assertIsNone(device1.path)
        self.assertIsNone(device1.device_id)

        device2 = conf.devices[1]
        self.assertEqual(device2.name, "scanner2")
        self.assertEqual(device2.type, "evdev")
        self.assertEqual(device2.path, "/dev/input/event0")
        self.assertEqual(device2.publisher.type, "stdout")

    def test_config_device_publisher_defaults(self):
        config_dict = {"erie": {"devices": [{"name": "test", "type": "stdin", "publisher": {}}]}}

        conf = Config.from_dict(config_dict)
        publisher = conf.devices[0].publisher

        self.assertEqual(publisher.type, "redis")
        self.assertEqual(publisher.host, "localhost")
        self.assertEqual(publisher.channel, "erie")

    def test_config_from_yaml(self):
        yaml_content = """
erie:
  name: yaml-test
  devices:
    - name: dev1
      type: serial
      path: /dev/ttyUSB0
      publisher:
        type: redis
        host: redis.example.com
        channel: scanner
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            tmp_path = f.name

        try:
            conf = Config.from_yaml(tmp_path)
            self.assertEqual(conf.name, "yaml-test")
            self.assertEqual(len(conf.devices), 1)
            self.assertEqual(conf.devices[0].name, "dev1")
            self.assertEqual(conf.devices[0].type, "serial")
            self.assertEqual(conf.devices[0].path, "/dev/ttyUSB0")
        finally:
            os.unlink(tmp_path)

    def test_config_from_json(self):
        json_content = '{"erie": {"name": "json-test"}}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            tmp_path = f.name

        try:
            conf = Config.from_json(tmp_path)
            self.assertEqual(conf.name, "json-test")
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()

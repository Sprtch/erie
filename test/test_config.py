from erie.config import Config
from erie.devices.stdindevice import StdinWrapper
import unittest


class TestConfig(unittest.TestCase):
    def test_config_test_printer(self):
        config_dict = {
            "erie": {
                "redis": "victoria",
                "devices": [{
                    "stdin": {
                        "type": "stdin",
                    }
                }]
            }
        }

        conf = Config.from_dict(config_dict)
        self.assertEqual(conf.redis, 'victoria')
        self.assertFalse(conf.debug)
        self.assertEqual(len(conf.devices), 1)
        device = conf.devices[0]
        self.assertTrue(isinstance(device, StdinWrapper))
        self.assertEqual(device.name, 'stdin')
        self.assertEqual(device.redis, 'victoria')


if __name__ == '__main__':
    unittest.main()

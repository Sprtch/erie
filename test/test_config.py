from erie.config import Config
from erie.devices.stdindevice import StdinWrapper
from despinassy.Scanner import Scanner as ScannerTable
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

        self.assertEqual(ScannerTable.query.count(), 1)
        s = ScannerTable.query.get(1)
        self.assertIsNotNone(s)
        self.assertEqual(s.type, device.get_type())
        self.assertEqual(s.name, device.name)
        self.assertEqual(s.settings, device.export_config())


if __name__ == '__main__':
    unittest.main()
import unittest
import unittest.mock
import builtins
from erie.devices.stdindevice import StdinWrapper


class TestDevice(unittest.TestCase):
    def test_device_stdin(self):
        device = StdinWrapper("stdin", "test")

        self.assertEqual(device.present(), True)
        with unittest.mock.patch.object(builtins, 'input',
                                        lambda: 'helloworld'):
            gen = device.retrieve()
            output = next(gen)
            self.assertEqual(output, 'HELLOWORLD')


if __name__ == '__main__':
    unittest.main()

import unittest
from erie.processor.base import Processor
from erie.schema.message import IpcIncompleteMessage, IpcPrintMessage
from erie.schema.type import ScannerModeEnum


class TestProcessor(unittest.TestCase):
    def setUp(self):
        self.proc = Processor()

    def test_initial_state(self):
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertIsNotNone(result)
        self.assertEqual(result.content, "FOO1234BAR")
        self.assertEqual(result.type, ScannerModeEnum.PRINTMODE)

    def test_processor_barcode(self):
        msg = IpcIncompleteMessage(content="FOO1234BAR", device="test")
        result = self.proc.read(msg)
        self.assertIsNotNone(result)
        self.assertEqual(result.content, "FOO1234BAR")
        self.assertEqual(result.type, ScannerModeEnum.PRINTMODE)

    def test_processor_multiplier(self):
        multiplier_msg = IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test")
        barcode_msg = IpcIncompleteMessage(content="FOO1234BAR", device="test")
        self.proc.read(multiplier_msg)
        result = self.proc.read(barcode_msg)
        self.assertIsNotNone(result)
        self.assertEqual(result.content, "FOO1234BAR")
        self.assertEqual(result.quantity, "2")

        self.proc = Processor()
        multiplier_msg = IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:4", device="test")
        barcode_msg = IpcIncompleteMessage(content="FOO1234BAR", device="test")
        self.proc.read(multiplier_msg)
        result = self.proc.read(barcode_msg)
        self.assertEqual(result.quantity, "4")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "8")

    def test_processor_clear(self):
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:CLEAR:0", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "1")

    def test_processor_negative(self):
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:NEGATIVE:0", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "-4")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:NEGATIVE:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:4", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "-4")

    def test_processor_digit(self):
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "42")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "42")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "84")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "82")

    def test_processor_dotted(self):
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:4", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DOTTED:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "4.2")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DOTTED:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "0.2")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DOTTED:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "0.4")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DOTTED:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "0.42")

        self.proc = Processor()
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DOTTED:0", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MULTIPLIER:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:DIGIT:2", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:NEGATIVE:0", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertEqual(result.quantity, "-0.42")

    def test_processor_mode_inventory(self):
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MODE:INVENTORY", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertIsNotNone(result)
        self.assertEqual(result.type, ScannerModeEnum.INVENTORYMODE)

    def test_processor_mode_print(self):
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MODE:INVENTORY", device="test"))
        self.proc.read(IpcIncompleteMessage(content="SPRTCHCMD:MODE:PRINT", device="test"))
        result = self.proc.read(IpcIncompleteMessage(content="FOO1234BAR", device="test"))
        self.assertIsNotNone(result)
        self.assertEqual(result.type, ScannerModeEnum.PRINTMODE)

    def test_match_invalid_command(self):
        result = self.proc.match("SPRTCHCMD:INVALID")
        self.assertIsNone(result)

    def test_match_non_command(self):
        result = self.proc.match("FOO1234BAR")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

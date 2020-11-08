from despinassy import Part
from erie.message import BarcodeMessage, Message

class Scanner:
    @staticmethod
    def retrieve_from_db(msg):
        in_db = Part.query.get(msg.barcode)
        if in_db:
            return Message(name=in_db.name, **msg._asdict())
        else:
            return Message(message='', **msg._asdict())

    @staticmethod
    def process(msg):
        return Scanner.retrieve_from_db(msg)

class Processor:
    def __init__(self, dev):
        self.dev = dev
        self.mode = Scanner

    def read(self):
        for msg in self.dev.read_loop():
            yield self.mode.process(msg)

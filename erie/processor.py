from despinassy import Part
from erie.message import BarcodeMessage, Message
from erie.logger import logger

class Scanner:
    @staticmethod
    def retrieve_from_db(msg):
        in_db = Part.query.filter(Part.barcode == msg.barcode).first()
        if in_db:
            msg = Message(name=in_db.name, **msg._asdict())
            logger.info("[%s] Scanned '%s' and found '%s'" % (msg.origin, msg.barcode, msg.name))
        else:
            msg = Message(name='', **msg._asdict())
            logger.info("[%s] Scanned '%s'" % (msg.origin, msg.barcode))
        return msg

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

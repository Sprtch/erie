from despinassy import Part, Inventory, db
from despinassy.ipc import create_nametuple
from erie.message import Message
from erie.logger import logger

class ProcessorMode:
    @staticmethod
    def process(msg: Message) -> Message:
        raise NotImplementedError

class PrintModeProcessor(ProcessorMode):
    @staticmethod
    def process(msg: Message) -> Message:
        in_db = Part.query.filter(Part.barcode == msg.barcode).first()
        if in_db:
            msg = create_nametuple(Message, msg._asdict(), name=in_db.name)
            logger.info("[%s] Scanned '%s' and found '%s'" % (msg.origin, msg.barcode, msg.name))
        else:
            msg = create_nametuple(Message, msg._asdict(), name='')
            logger.info("[%s] Scanned '%s'" % (msg.origin, msg.barcode))
        return msg

class InventoryModeProcessor(ProcessorMode):
    @staticmethod
    def process(msg: Message) -> Message:
        return msg


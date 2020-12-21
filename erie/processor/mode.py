from despinassy import Part, Inventory, db
from despinassy.ipc import create_nametuple, redis_subscribers_num, ipc_create_print_message, IpcOrigin
from erie.message import Message
from erie.logger import logger
from redis import ConnectionError, Redis
import json

r = Redis(host='localhost', port=6379, db=0)
p = r.pubsub()


class ProcessorMode:
    def process(self, msg: Message) -> Message:
        raise NotImplementedError


class PrintModeProcessor(ProcessorMode):
    def execute(self, msg: Message):
        try:
            ipc_msg = ipc_create_print_message(
                msg, number=int(msg.number), origin=IpcOrigin.ERIE)._asdict()
            if redis_subscribers_num(r, msg.redis):
                r.publish(msg.redis, json.dumps(ipc_msg))
            else:
                logger.warning(
                    "[%s] No recipient on channel '%s' for the message: ''%s'"
                    % (msg.device, msg.redis, json.dumps(ipc_msg)))
        except ConnectionError as e:
            logger.error(e)

    def process(self, msg: Message):
        in_db = Part.query.filter(Part.barcode == msg.barcode).first()
        if in_db:
            msg = create_nametuple(Message, msg._asdict(), name=in_db.name)
            logger.info("[%s] Scanned '%s' and found '%s'" %
                        (msg.device, msg.barcode, msg.name))
        else:
            msg = create_nametuple(Message, msg._asdict(), name='')
            logger.info("[%s] Scanned '%s'" % (msg.device, msg.barcode))

        self.execute(msg)


class InventoryModeProcessor(ProcessorMode):
    def process(self, msg: Message):
        in_db = Part.query.filter(Part.barcode == msg.barcode).first()
        if in_db:
            msg = create_nametuple(Message, msg._asdict(), name=in_db.name)
            i = None
            if len(in_db.inventories):
                i = in_db.inventories[0]
                i.add(msg.number)
            else:
                i = Inventory(part=in_db, quantity=msg.number)
                db.session.add(i)
            logger.info("[%s] '%s' added %i time to Inventory (now %i entry)" %
                        (msg.device, msg.barcode, msg.number, i.quantity))
            db.session.commit()
        else:
            logger.warning("[%s] Barcode '%s' not found" %
                           (msg.device, msg.barcode))

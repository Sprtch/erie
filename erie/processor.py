class Scanner:
    @staticmethod
    def retrieve_from_db(msg):
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

from collections import namedtuple

Message = namedtuple('BarcodeMessage', 'barcode, origin, redis, name, number', defaults=(None, None, None, '', 1))

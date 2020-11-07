from collections import namedtuple

BarcodeMessage = namedtuple('BarcodeMessage', 'barcode, origin, redis')
Message = namedtuple('BarcodeMessage', 'barcode, origin, redis, name')

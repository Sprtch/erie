import logging

logger = logging.getLogger("erie")


def init_log(config):
    formatter = logging.Formatter(fmt='[%(asctime)s] %(message)s',
                                  datefmt='%m/%d/%Y %I:%M:%S %p')
    loglevel = logging.DEBUG if config.debug else logging.INFO
    logger.setLevel(loglevel)

    if config.logfile:
        fh = logging.FileHandler(config.logfile, "w")
        fh.setLevel(loglevel)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        fh = logging.StreamHandler()
        fh.setLevel(loglevel)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

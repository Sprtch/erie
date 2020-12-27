from despinassy import db
import dataclasses


def init_db(config={}):
    dict_config = dataclasses.asdict(config)
    db.init_app(config=dict_config)

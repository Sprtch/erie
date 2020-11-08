from despinassy import db

def init_db(config={}):
    db.init_app(config=config)

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = ''  # os.urandom(24)


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class DB(object):
    db = ''
    host = 'localhost'
    port = None
    username = None
    password = None

class MongoDB(DB):
    """URL FORMAT - mongodb://username:password@host:port/database?options"""
    db = 'attendance-system'
    host = 'localhost'
    port = 27017
    username = ''
    password = ''
    url = "mongodb://{}:{}@{}:{}/{}".format(
        username, password, host, port, db)


class RedisDB(DB):
    """URL FORMAT - redis://:password@hostname:port/db_number"""
    host = ''
    port = 18772
    username = ''
    password = ''
    url = "redis://:{}@{}:{}/{}".format(
        password, host, port, 0)

# -*- coding: utf-8 -*-

APP_NAME = 'hunchkin'

class BaseConfig(object):

    DEBUG = False
    TESTING = False

    # os.urandom(24)
    SECRET_KEY = 'secret key'


class DefaultConfig(BaseConfig):

    DEBUG = True

    SQLALCHEMY_ECHO = True
    # Sqlite
    #SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/fbone.db'
    SQLALCHEMY_DATABASE_URI = 'mysql://appuser:rextrebat@localhost/hotel_genome'
    # Mysql: 'mysql://dbusername:dbpassword@dbhost/dbname'

    # To create log folder.
    # $ sudo mkdir -p /var/log/fbone
    # $ sudo chown $USER /var/log/fbone
    DEBUG_LOG = '/var/log/hunchkin/debug.log'

    ACCEPT_LANGUAGES = ['zh']
    BABEL_DEFAULT_LOCALE = 'en'

    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 60

    # Email (Flask-email)
    # https://bitbucket.org/danjac/flask-mail/issue/3/problem-with-gmails-smtp-server
    MAIL_DEBUG = DEBUG
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'support'
    MAIL_PASSWORD = 'HKsupport'
    DEFAULT_MAIL_SENDER = '%s@hunchkin.com' % MAIL_USERNAME

    HOST="localhost"
    USERNAME = "appuser"
    PASSWORD = "rextrebat"
    DB = "hotel_genome"

    SOCIAL_FACEBOOK = {
            'consumer_key': '401915129878375',
            'consumer_secret': '087ada986d6c5a54e98ac7d28416b3c5',
            }
    SOCIAL_URL_PREFIX = "/social/"
    SOCIAL_BLUEPRINT_NAME = "social"

    FACEBOOK_APP_ID = '401915129878375'
    FACEBOOK_APP_SECRET = '087ada986d6c5a54e98ac7d28416b3c5'


class TestConfig(BaseConfig):
    TESTING = True
    CSRF_ENABLED = False

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'

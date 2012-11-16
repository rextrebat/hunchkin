#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Webapp
from fbone template_filter
https://github.com/imwilsonxu/fbone.git
"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import pymongo
from flask import Flask, g
import urllib

from webapp import utils
from webapp.config import DefaultConfig
from webapp.views import search, browse_genome
from webapp.models import User
from webapp.extensions import db, mail, cache, login_manager

# configuration

app = Flask(__name__)

# Configure app from config
app.config.from_object(DefaultConfig)

# Register blueprints
app.register_blueprint(search)
app.register_blueprint(browse_genome)

# configure extensions
# sqlalchemy
db.init_app(app)
# mail
mail.init_app(app)
# cache
cache.init_app(app)
# login
login_manager.login_view = 'frontend.login'
login_manager.refresh_view = 'frontend.reauth'
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
login_manager.setup_app(app)

# Configure logging

if app.debug or app.testing:
    pass
else:
    import logging
    import os

    app.logger.setLevel(logging.INFO)

    debug_log = os.path.join(app.root_path, app.config['DEBUG_LOG'])
    file_handler = logging.handlers.RotatingFileHandler(
            debug_log,
            maxBytes=100000,
            backupCount=10
            )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
        )
    app.logger.addHandler(file_handler)
    ADMINS = ['kd@gmail.com']
    mail_handler = logging.handlers.SMTPHandler(
            app.config['MAIL_SERVER'],
            app.config['MAIL_USERNAME'],
            ADMINS,
            'O_ops...Hunchkin failed!',
            (
                app.config['MAIL_USERNAME'],
                app.config['MAIL_PASSWORD']
                )
            )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
        )
    app.logger.addHandler(mail_handler)


#
@app.template_filter('urlquote')
def urlquote(s):
   return urllib.quote(s)
app.jinja_env.globals['urlquote'] = urlquote


@app.template_filter()
def pretty_date(value):
    return utils.pretty_date(value)


def connect_db():
    return MySQLdb.Connection(
            host=app.config['HOST'],
            db=app.config['DB'],
            user=app.config['USERNAME'],
            passwd=app.config['PASSWORD']
            )

def connect_mongo():
    return pymongo.Connection(host=app.config['HOST'])


@app.before_request
def before_request():
    g.db = connect_db()
    g.mongo = connect_mongo()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

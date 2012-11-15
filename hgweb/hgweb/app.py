#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""[application description here]"""

__author__ = "Kingshuk Dasgupta (rextrebat/kdasgupta)"
__version__ = "0.0pre0"

import MySQLdb
import pymongo
from flask import Flask, g
from views import search, browse_genome
import urllib

# configuration

app = Flask(__name__)

app.config.update(
DEBUG=True,
SECRET_KEY = "development key",
HOST="localhost",
USERNAME = "appuser",
PASSWORD = "rextrebat",
DB = "hotel_genome",
)

app.register_blueprint(search)
app.register_blueprint(browse_genome)

@app.template_filter('urlquote')
def urlquote(s):
   return urllib.quote(s)
app.jinja_env.globals['urlquote'] = urlquote


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

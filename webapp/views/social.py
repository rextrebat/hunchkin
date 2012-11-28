# -*- coding: utf-8 -*-

from flask.ext.social import Social
from flask.ext.social.datastore import SQLAlchemyConnectionDatastore
from webapp.extensions import db

social = Social(db, Connection)

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
import pylibmc
from flask import Flask, g, render_template
from flask_debugtoolbar import DebugToolbarExtension
import urllib
from flask.ext.babel import Babel
from flask.ext.security import Security
#from flask.ext.social import Social
from flask.ext.security import SQLAlchemyUserDatastore
#from flask.ext.social.datastore import SQLAlchemyConnectionDatastore
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from beaker.middleware import SessionMiddleware

from webapp import utils
from webapp.config import DefaultConfig, APP_NAME
from webapp.views import search, browse_genome, frontend, social, GenomeRuleView, GenomeCategoryView
from webapp.models import User, Role, Connection, GenomeRule, GenomeCategory
from webapp.extensions import db, db_ean, mail, cache, login_manager
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# For import *
__all__ = ['create_app']

DEFAULT_BLUEPRINTS = (
    browse_genome,
    search,
    frontend,
    social,
    )


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""

    if app_name is None:
        app_name = APP_NAME
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    #app = Flask(app_name)
    app = Flask(__name__)
    configure_app(app, config)
    configure_hook(app)
    configure_session(app)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    configure_logging(app)
    configure_template_filters(app)
    configure_error_handlers(app)

    return app



def configure_app(app, config):
    """Configure app from object, parameter and env."""

    app.config.from_object(DefaultConfig)
    if config is not None:
        app.config.from_object(config)


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_session(app):
    """Configure Beaker session"""
    app.wsgi_app = SessionMiddleware(app.wsgi_app, app.config['SESSION_OPTS'])


def configure_extensions(app):
# configure extensions
# sqlalchemy
    db.init_app(app)
    db_ean.init_app(app)
# mail
    mail.init_app(app)
# cache
    cache.init_app(app)
# babel
    babel = Babel(app)
# login
    login_manager.login_view = 'frontend.login'
    login_manager.refresh_view = 'frontend.reauth'
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    login_manager.setup_app(app)
# security and Social
    app.flask_security = Security(app, SQLAlchemyUserDatastore(db, User, Role))
    #app.flask_social = Social(app, SQLAlchemyConnectionDatastore(db, Connection))
# admin
    admin = Admin(app)
    #admin.add_view(ModelView(GenomeRule, db.session))
    admin.add_view(GenomeRuleView(db.session, name="Genome Rules"))
    admin.add_view(GenomeCategoryView(db.session, name="Genome Categories"))

# Configure logging

def configure_logging(app):
    """Configure file(info) and email(error) logging."""

    if app.debug or app.testing:
        toolbar = DebugToolbarExtension(app)
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
def configure_template_filters(app):
    @app.template_filter('urlquote')
    def urlquote(s):
        return urllib.quote(s)

    app.jinja_env.globals['urlquote'] = urlquote


    @app.template_filter()
    def pretty_date(value):
        return utils.pretty_date(value)



def configure_hook(app):

    def connect_db():
        return MySQLdb.Connection(
                host=app.config['HOST'],
                db=app.config['DB'],
                user=app.config['USERNAME'],
                passwd=app.config['PASSWORD']
                )

    def connect_db_ean():
        return MySQLdb.Connection(
                host=app.config['EAN_HOST'],
                db=app.config['EAN_DB'],
                user=app.config['EAN_USERNAME'],
                passwd=app.config['EAN_PASSWORD']
                )

    def connect_mongo():
        return pymongo.Connection(host=app.config['HOST'])

    def connect_memcached():
        return pylibmc.Client([app.config['MEMCACHED_SERVER']], binary=True,
                behaviors={"tcp_nodelay": True, "ketama": True})

    @app.before_request
    def before_request():
        g.db = connect_db()
        g.db_ean = connect_db_ean()
        g.mongo = connect_mongo()
        g.mc = connect_memcached()


    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db'):
            g.db.close()
        if hasattr(g, 'db_ean'):
            g.db_ean.close()


def configure_error_handlers(app):

    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("errors/forbidden_page.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/page_not_found.html"), 404

    @app.errorhandler(405)
    def method_not_allowed_page(error):
        return render_template("errors/method_not_allowed.html"), 405

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/server_error.html"), 500

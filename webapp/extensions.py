# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask.ext.mail import Mail
mail = Mail()

from flask.ext.cache import Cache
cache = Cache()

from flask.ext.login import LoginManager
login_manager = LoginManager()

from flask_oauth import OAuth
from webapp.config import DefaultConfig
oauth = OAuth()

#facebook = oauth.remote_app('facebook',
    #base_url='https://graph.facebook.com/',
    #request_token_url=None,
    #access_token_url='/oauth/access_token',
    #authorize_url='https://www.facebook.com/dialog/oauth',
    #consumer_key=DefaultConfig.FACEBOOK_APP_ID,
    #consumer_secret=DefaultConfig.FACEBOOK_APP_SECRET,
    #request_token_params={'scope': 'email'}
#)

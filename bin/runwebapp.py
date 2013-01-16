#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask.ext.script import Manager, Command
from gevent.wsgi import WSGIServer

from webapp import create_app
from webapp.extensions import db
from webapp.models import User

manager = None
app = None


def init_manager(config=None):
    global manager
    global app
    app = create_app(config)
    manager = Manager(app)
    project_root_path = os.path.join(os.path.dirname(app.root_path))
    manager.add_command('run', RunServer())
    manager.add_command('reset', Reset())

class RunServer(Command):
    """Run Server"""

    def run(self):
        http_server = WSGIServer(('0.0.0.0', 5000), app)
        http_server.serve_forever()
        #app.run(host='0.0.0.0', debug=True)


class Reset(Command):
    """Reset Database"""

    def run(self):
        db.drop_all()
        db.create_all()
        user = User(name='tester', email='tester@hunchkin.com', password='123456')
        db.session.add(user)
        db.session.commit()


if __name__ == "__main__":

    import sys
    import ConfigParser

    config = ConfigParser.RawConfigParser()
    try:
        config.read('/etc/hunchkin.conf')
        env = config.get('environment', 'env')
        if env == "DEV":
            from webapp.config import DevConfig
            config = DevConfig
        elif env == "PROD":
            from webapp.config import ProdConfig
            config = ProdConfig
        else:
            raise RuntimeError("Environment not defined")
    except:
        print "Cannot determine environment..exiting"
        sys.exit(1)
    init_manager(config)
    manager.run()

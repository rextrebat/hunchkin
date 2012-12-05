#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask.ext.script import Manager
from gevent.wsgi import WSGIServer

from webapp import create_app
from webapp.extensions import db
from webapp.models import User



manager = Manager(create_app())

app = create_app()
project_root_path = os.path.join(os.path.dirname(app.root_path))


@manager.command
def run():
    """Run local server."""

    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
    #app.run(host='0.0.0.0', debug=True)


@manager.command
def reset():
    """Reset database."""

    db.drop_all()
    db.create_all()
    user = User(name='tester', email='tester@hunchkin.com', password='123456')
    db.session.add(user)
    db.session.commit()


manager.add_option('-c', '--config',
                   dest="config",
                   required=False,
                   help="config file")

if __name__ == "__main__":
    manager.run()

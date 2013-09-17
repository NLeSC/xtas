from functools import wraps

from celery import Celery
from flask import Flask

from .taskregistry import TASKS
from . import tasks


class Server(object):
    """xtas front-end server/WSGI app."""

    def __init__(self, broker='amqp://guest@localhost//', debug=False,
                 port=5000):
        self.broker = broker
        self.debug = debug
        self.port = port

    def run(self):
        # We turn off the reloader because it doesn't seem to work with our
        # package structure: it complains about relative imports.
        wsgi = Flask('xtas')
        taskq = Celery(broker=self.broker, backend='amqp')

        if self.debug:
            print('Registered tasks:')
            for f, url in TASKS:
                print("%s at %s" % (f.__name__, url))

        for f, url in TASKS:
            #f = taskq.task(f)
            wsgi.route(url)(f)

        self._wsgi = wsgi
        self._taskq = taskq

        # Celery starts running immediately, so no run for taskq
        wsgi.run(debug=self.debug, use_reloader=False)

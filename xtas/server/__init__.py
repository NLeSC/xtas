from copy import deepcopy
from functools import partial, wraps

from celery import Celery
from flask import Flask, request
import simplejson as json

from .. import elastic      # noqa
from ..taskregistry import ASYNC_TASKS, SYNC_TASKS
from .. import tasks        # noqa
from ..util import getconf


class Server(object):
    """xtas front-end server/WSGI app.

    Constructing a Server only configures it. To actually run the Server,
    call the run method.

    Parameters
    ----------
    broker : string, optional
        URL of broker instance for Celery. By default, connects to RabbitMQ
        on localhost.
    debug : boolean, optional
        Turn debugging on. Since this enables Flask debugging, it's a
        potential security hazard, so don't enable it in production.
    port : integer
        Port number of REST API.
    """
    # XXX the parameters above are now passed inside config as keys,
    # need a systematic way to document this.

    def __init__(self, config):
        self.config = deepcopy(config)

    def run(self):
        conf = partial(getconf, self.config, error='raise')

        broker = conf('main broker')
        self.debug = conf('server debug')
        port = conf('server port')

        wsgi = Flask('xtas')
        taskq = Celery(broker=broker, backend='amqp')
        taskq.conf.CELERY_ALWAYS_EAGER = conf('server local')

        if self.debug:
            print('Registered tasks:')
            for f, url, _ in ASYNC_TASKS:
                print("%s at %s" % (f.__name__, url))

        for f, url, methods in ASYNC_TASKS:
            # We explicitly set the name because automatic naming and relative
            # imports don't go well (http://tinyurl.com/tasknaming).
            f = taskq.task(f, name=url)
            f = self._delay(f)
            wsgi.add_url_rule(url, f.__name__, f, methods=methods)

        for f, url, methods in SYNC_TASKS:
            # Partials don't have an __name__, but Flask wants one.
            name = f.__name__
            f = partial(f, config=self.config)

            wsgi.add_url_rule(url, name, f, methods=methods)

        wsgi.route('/result/<task_id>')(self._force)

        self._wsgi = wsgi
        self._taskq = taskq

        # Celery starts running immediately, so no run for taskq.
        # We turn off the reloader because it doesn't seem to work with our
        # package structure: it complains about relative imports.
        wsgi.run(debug=self.debug, port=port, use_reloader=False)

    def _delay(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f.delay(*args, config=self.config, **kwargs).task_id

        return wrapper

    def _force(self, task_id):
        """Force execution of task_id and return its results."""

        if self.debug:
            print('Forcing result for %s' % task_id)

        return json.dumps(self._taskq.AsyncResult(task_id).get())

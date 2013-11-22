from copy import deepcopy
from functools import partial, wraps

from celery import Celery
from flask import Flask, render_template
import simplejson as json

from .. import elastic      # noqa
from ..taskregistry import ASYNC_TASKS, SYNC_TASKS
from ..util import getconf, import_plugins


class Server(object):
    """xtas front-end server/WSGI app.

    Constructing a Server only configures it. To actually run the Server,
    call the run method.

    Be sure to never construct multiple Servers that talk to the same broker,
    not even in separate processes.

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
        import_plugins(config)

    def run(self):
        conf = partial(getconf, self.config, error='raise')

        broker = conf('main broker')
        self.debug = conf('server debug')
        port = conf('server port')

        wsgi = Flask('xtas')
        taskq = Celery(broker=broker, backend='amqp')
        taskq.conf.CELERY_ALWAYS_EAGER = conf('server local', error='default')

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

        wsgi.add_url_rule('/', 'console', self._render_console)
        wsgi.route('/result/<task_id>')(self._force)
        wsgi.route('/state/<task_id>')(self._get_task_state)
        wsgi.route('/tasks')(self._task_list_json)

        wsgi.route('/empty_results')(self._clear_completed_tasks)

        self._wsgi = wsgi
        self._taskq = taskq

        # locally cached task list, to be updated each time Celery talks to
        # the broker
        self._tasklist = {}

        # Celery starts running immediately, so no run for taskq.
        # We turn off the reloader because it doesn't seem to work with our
        # package structure: it complains about relative imports.
        wsgi.run(debug=self.debug, port=port, use_reloader=False)

    def _delay(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            task_id = f.delay(*args, config=self.config, **kwargs).task_id
            self._tasklist[task_id] = {'state': 'QUEUEING'}
            return task_id

        return wrapper

    def _force(self, task_id):
        """Force execution of task_id and return its results."""

        if self.debug:
            print('Forcing result for %s' % task_id)

        if task_id in self._tasklist:
            del self._tasklist[task_id]

        return json.dumps(self._taskq.AsyncResult(task_id).get())

    def _get_task_state(self, task_id):
        """Retrieve and return state of of task_id."""
        state = self._taskq.AsyncResult(task_id).state

        if task_id in self._tasklist:
            self._tasklist[task_id]['state'] = state

        return state

    def _render_console(self):
        """Render the web console."""

        conf = partial(getconf, self.config)

        es = conf('main elasticsearch')
        rabbitmq = conf('main broker', '').startswith('amqp')
        debug = conf('main debug', False)

        return render_template('console.html',
                               rabbitmq=rabbitmq,
                               elasticsearch=es,
                               debug=debug,
                               tasks=self._task_list().items())

    def _task_list_json(self):
        return json.dumps(self._task_list())

    def _task_list(self):
        """Update and retrieve a list of active and reserved tasks."""

        inspector = self._taskq.control.inspect()
        active = inspector.active()
        reserved = inspector.reserved()

        found_tasks = []

        for node in active:
            for task in active[node]:
                if task['id'] not in found_tasks:
                    found_tasks.append(task['id'])
                if task['id'] in self._tasklist:
                    self._tasklist[task['id']]['state'] = 'RUNNING'
                    self._tasklist[task['id']]['details'] = task
            for task in reserved[node]:
                if task['id'] not in found_tasks:
                    found_tasks.append(task['id'])
                if task['id'] in self._tasklist:
                    self._tasklist[task['id']] = 'WAITING'
                    self._tasklist[task['id']]['details'] = task
        for id in self._tasklist:
            if id not in found_tasks:
                self._tasklist[id] = 'SUCCESS'

        return self._tasklist

    def _clear_completed_tasks(self):
        """Remove all results which have not been requested from the queue."""

        # update the task list
        self._task_list()

        # XXX should be using a control.revoke here
        for id in self._tasklist:
            if id['state'] == 'SUCCESS':
                self._force(id)

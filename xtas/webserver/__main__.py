from __future__ import absolute_import

import argparse
import json
import logging
from pprint import pprint
import sys

from celery import chain
from celery import __version__ as celery_version
import celery.result
from flask import Flask, Response, abort, request
from flask import __version__ as flask_version

from tornado import version as tornado_version
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from xtas import __version__
from xtas.tasks import app as taskq
from xtas.tasks import es_document, store_single

app = Flask(__name__)


@app.route("/")
def home():
    pyver = sys.version_info
    text = "xtas web server\n"
    if app.debug:
        text += '\n'.join(["\nPython version %d.%d.%d"
                               % (pyver.major, pyver.minor, pyver.micro),
                           "Celery version %s" % celery_version,
                           "Flask version %s" % flask_version,
                           "Tornado version %s" % tornado_version])
    return Response(text, mimetype="text/plain")


def _get_task(taskname):
    # XXX custom tasks could be batch tasks, but we don't check for that.
    try:
        if '.' not in taskname:
            taskname = 'xtas.tasks.single.%s' % taskname
        return taskq.tasks[taskname]
    except KeyError:
        if app.debug:
            raise
        else:
            abort(404)


@app.route('/run/<taskname>', methods=['POST'])
def run_task(taskname):
    """Run named task on a document fed as POST data.

    The POST data should have Content-type text/plain or application/json.
    """
    task = _get_task(taskname)
    data = request.data

    content_type = request.headers['Content-Type']
    if content_type == 'text/plain':
        return task.delay(request.data).id + "\n"

    elif content_type == 'application/json':
        data = request.json['data']
        kwargs = request.json.get('arguments', {})
        return task.delay(data, **kwargs).id + "\n"

    abort(404)  # XXX this is not the right error code


@app.route("/run_es/<taskname>/<index>/<type>/<id>/<field>")
def run_task_on_es(taskname, index, type, id, field):
    """Run named task on single document given by (index, type, id, field).

    taskname must be the fully qualified name of a function, except for
    built-in xtas.tasks.single tasks, which are addressed by their short name.

    Only works for tasks in xtas.tasks.single and custom tasks, not clustering
    tasks.
    """
    # XXX custom tasks could be batch tasks, but we don't check for that.
    task = _get_task(taskname)
    return chain(task.s(es_document(index, type, id, field))
                 | store_single.s(taskname, index, type, id)
                 ).delay().id + "\n"


@app.route('/result/<jobid>')
def result(jobid):
    return json.dumps(celery.result.AsyncResult(jobid).get()) + "\n"


@app.route('/tasks')
def show_tasks():
    tasknames = sorted(t.split('.', 3)[-1] if t.startswith('xtas.tasks') else t
                       for t in taskq.tasks
                       if not t.startswith('celery.'))
    return json.dumps(tasknames)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="xtas web server")
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Enable debugging mode.')
    parser.add_argument('--host', dest='host', default='127.0.0.1',
                        help='Host to listen on.')
    parser.add_argument('--port', dest='port', default=5000, type=int,
                        help='Port to listen on.')
    parser.add_argument('--threads', dest='threads', default=5, type=int,
                        help='Number of threads.')
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=loglevel)

    app.debug = args.debug
    print("xtas %s REST endpoint" % __version__)
    if app.debug:
        print("Serving tasks:")
        pprint(list(taskq.tasks.keys()))
    http_server = HTTPServer(WSGIContainer(app))
    http_server.bind(args.port, address=args.host)
    http_server.start(args.threads)
    IOLoop.instance().start()

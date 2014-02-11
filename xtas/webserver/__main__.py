from __future__ import absolute_import

import argparse
import json
import logging
import sys

from celery import Task, chain
from celery import __version__ as celery_version
import celery.result
from flask import Flask, Response, abort
from flask import __version__ as flask_version

from ..tasks import app as taskq
from ..tasks import es_document, store_single

app = Flask(__name__)


@app.route("/")
def home():
    # XXX should do this only in debug mode or when key is given to prevent
    # attacks on specific Flask versions.
    pyver = sys.version_info
    text = '\n'.join(["xtas web server\n",
                      "Python version %d.%d.%d" % (pyver.major, pyver.minor,
                                                   pyver.micro),
                      "Celery version %s" % celery_version,
                      "Flask version %s" % flask_version])
    return Response(text, mimetype="text/plain")


@app.route("/run_es/<task>/<index>/<type>/<id>/<field>")
def run_task_on_es(task, index, type, id, field):
    try:
        taskname = 'xtas.tasks.%s' % task
        task = taskq.tasks[taskname]
    except KeyError:
        abort(404)

    return chain(task.s(es_document(index, type, id, field))
                 | store_single.s(taskname, index, type, id)
                ).delay().id


@app.route('/result/<jobid>')
def result(jobid):
    return json.dumps(celery.result.AsyncResult(jobid).get())


@app.route('/tasks')
def show_tasks():
    tasknames = sorted(t.split('.', 3)[-1] for t in taskq.tasks
                                           if t.startswith('xtas.tasks'))
    return json.dumps(tasknames)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="xtas web server")
    parser.add_argument('--debug', dest='debug', action='store_true')
    args = parser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=loglevel)

    app.debug = args.debug
    app.run()

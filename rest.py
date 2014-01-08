from __future__ import absolute_import

from celery import Task, chain
import celery.result
from flask import Flask, abort
import json

from xtas.tasks import app as taskq
from xtas.tasks import fetch_es, store_es

app = Flask(__name__)
app.debug = True


@app.route("/run_es/<task>/<index>/<type>/<id>/<field>")
def run_task_on_es(task, index, type, id, field):
    try:
        taskname = 'xtas.tasks.%s' % task
        task = taskq.tasks[taskname]
    except KeyError:
        abort(404)

    return chain(fetch_es.s(index, type, id, field)
                 | task.s()
                 | store_es.s(taskname, index, type, id)
                ).delay().id


@app.route('/tasks')
def show_tasks():
    return json.dumps([t.split('.', 3)[-1] for t in taskq.tasks
                                           if t.startswith('xtas.tasks')])


if __name__ == "__main__":
    app.run()

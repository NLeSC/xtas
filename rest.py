from __future__ import absolute_import

from flask import Flask, abort
import json
from xtas.tasks import app as taskq

app = Flask(__name__)


@app.route("/run_es/<task>/<index>/<type>/<id>")
def run_task_on_es(task, index, type, id):
    try:
        task = taskq.tasks['xtas.tasks.%s' % task]
    except KeyError:
        abort(404)

    return chain(fetch_es.s(index, type, id) | task).delay().id


@app.route('/tasks')
def show_tasks():
    return json.dumps([t.split('.', 3)[-1] for t in taskq.tasks
                                           if t.startswith('xtas.tasks')])


if __name__ == "__main__":
    app.run()

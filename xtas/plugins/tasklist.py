"""Returns a list of running tasks."""

from celery import Celery
import simplejson as json

from ..taskregistry import task
from ..util import getconf


@task(takes=None, sync=True)
def tasklist(config):
    broker = getconf(config, 'main broker')
    taskq = Celery(broker=broker, backend='amqp')
    inspect = taskq.control.inspect()

    tasks = {
        'active': inspect.active(),
        'reserved': inspect.reserved()
    }

    return json.dumps(tasks)

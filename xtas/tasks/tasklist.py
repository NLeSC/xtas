"""Simple tasks for testing and debugging."""

from celery import Celery
import time

from ..taskregistry import task
from ..util import getconf
import simplejson as json


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
    
    

# Worker main file. To run:
#   python -m xtas.worker

from __future__ import print_function
from argparse import ArgumentParser
from celery import Celery

from ..taskregistry import TASKS


argp = ArgumentParser(description='xtas worker')
argp.add_argument('--debug', action='store_true')

args = argp.parse_args()

# TODO add options for these
celery = Celery(broker='amqp://guest@localhost//', backend='amqp')

for f, url in TASKS:
    if args.debug:
        print("Providing task %s" % url)
    celery.task(f, name=url)

celery.worker_main()

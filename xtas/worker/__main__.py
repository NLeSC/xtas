# Worker main file. To run:
#   python -m xtas.worker

from __future__ import print_function
from argparse import ArgumentParser
from celery import Celery
import sys
import yaml

from ..taskregistry import TASKS
from .. import tasks        # noqa
from ..util import getconf


argp = ArgumentParser(description='xtas worker', prog='xtas.worker')
argp.add_argument('--config', default='xtas.yaml', dest='config',
                  help='Path to configuration file.')
argp.add_argument('--debug', action='store_true', dest='debug')
args = argp.parse_args()

# Hack: Celery mucks with sys.argv, and complains about our custom arguments.
del sys.argv[1:]

with open(args.config) as f:
    config = yaml.load(f)

config.setdefault('worker', {})['debug'] = args.debug

celery = Celery(broker=getconf(config, 'main broker'),
                backend=getconf(config, 'worker backend'))

for f, url in TASKS:
    if args.debug:
        print("Providing task %s" % url)
    celery.task(f, name=url)

celery.worker_main()

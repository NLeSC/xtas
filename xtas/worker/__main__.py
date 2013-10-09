# Worker main file. To run:
#   python -m xtas.worker

from __future__ import print_function
from argparse import ArgumentParser
from celery import Celery
import yaml

from ..taskregistry import TASKS
from ..util import getconf


argp = ArgumentParser(description='xtas worker')
argp.add_argument('--config', default='xtas.yaml', dest='config',
                  help='Path to configuration file.')
argp.add_argument('--debug', action='store_true')
args = argp.parse_args()

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

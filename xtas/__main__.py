from __future__ import print_function

from argparse import ArgumentParser
import sys

from celery import Celery

from .server import Server


def server_main():
    argp = ArgumentParser(description='xtas-lite server')
    argp.add_argument('--debug', action='store_true')

    args = argp.parse_args()

    server = Server(debug=args.debug)
    server.run()


def worker_main():
    argp = ArgumentParser(description='xtas-lite worker')
    argp.add_argument('--debug', action='store_true')

    args = argp.parse_args()

    from .taskregistry import TASKS
    from . import tasks

    # TODO add options for these
    celery = Celery(broker='amqp://guest@localhost//', backend='amqp')

    for f, url in TASKS:
        if args.debug:
            print("Providing task %s" % url)
        celery.task(f, name=url)

    celery.worker_main()


progs = {'server': server_main,
         'worker': worker_main}

try:
    main = progs[sys.argv.pop(1)]
    main()
except IndexError, KeyError:
    # XXX use argparse to handle this as well? docopt.org can do it...
    print('usage: python -m xtas (server|worker) [options]', file=sys.stderr)
    sys.exit(1)

from argparse import ArgumentParser
import os

from celery.bin.worker import worker

from .core import app


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--loglevel', dest='loglevel', default='WARN')
    parser.add_argument('--pidfile', dest='pidfile')
    args = parser.parse_args()

    if args.pidfile is not None:
        # XXX use 'x' in Python 3
        with open(args.pidfile, 'w') as pidfile:
            pidfile.write(str(os.getpid()))

    w = worker(app=app)
    w.run(loglevel=args.loglevel)

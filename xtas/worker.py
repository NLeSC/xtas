from argparse import ArgumentParser
import logging
import os

from celery.bin.worker import worker


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--loglevel', dest='loglevel', default='WARN',
                        help='Set minimum severity level of logger,'
                             ' e.g. DEBUG, ERROR, INFO. Default=WARNING.')
    parser.add_argument('--pidfile', dest='pidfile',
                        help='Write PID of worker to PIDFILE'
                             ' (not removed at shutdown!).')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel.upper())

    if args.pidfile is not None:
        # XXX use 'x' in Python 3
        with open(args.pidfile, 'w') as pidfile:
            logging.info('Writing PID to %s' % args.pidfile)
            pidfile.write(str(os.getpid()))

    # This import must be done after we've parsed the cmdline args and set
    # the logging level.
    from .core import app

    w = worker(app=app)
    w.run(loglevel=args.loglevel)

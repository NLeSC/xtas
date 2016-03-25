# Copyright 2013-2015 Netherlands eScience Center and University of Amsterdam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""xtas worker

Usage:
    xtas.worker [options]

Options:
  -h, --help           show this help message and exit
  --loglevel=LOGLEVEL  Set minimum severity level of logger, e.g. DEBUG,
                       ERROR, INFO. [default: WARNING].
  --pidfile=PIDFILE    Write PID of worker to PIDFILE (not removed at
                       shutdown!).
  --version            Print version info and exit.

"""

from __future__ import print_function

import logging
import os
import sys

from celery.bin.worker import worker
from docopt import docopt

from . import __version__


if __name__ == '__main__':
    args = docopt(__doc__)

    loglevel = args['--loglevel'].upper()
    logging.basicConfig(level=loglevel)

    pidfilepath = args.get('--pidfile')
    if pidfilepath is not None:
        # XXX use 'x' in Python 3
        with open(pidfilepath, 'w') as pidfile:
            logging.info('Writing PID to %s' % pidfilepath)
            pidfile.write(str(os.getpid()))

    # This import must be done after we've parsed the cmdline args and set
    # the logging level.
    from .core import app

    if args.get('--version'):
        print("xtas %s" % __version__)
        print("Celery", end=" ")
        app.worker_main(["--version"])
        sys.exit()

    # XXX app.worker_main is prettier but doesn't seem to respond to --loglevel
    worker(app=app).run(loglevel=loglevel)

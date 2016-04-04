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

"""xtas web server/REST API

Usage:
  webserver [options]

Options:
  -h, --help         show this help message and exit
  --debug            Enable debugging mode.
  --host=HOST        Host to listen on [default: 127.0.0.1].
  --port=PORT        Port to listen on [default: 5000].
  --threads=THREADS  Number of threads [default: 5].

"""

from __future__ import absolute_import
from pprint import pprint

import logging

from docopt import docopt

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from . import app
from xtas import __version__
from xtas.tasks import app as taskq

args = docopt(__doc__)

loglevel = logging.DEBUG if args.get('--debug') else logging.INFO
logging.basicConfig(level=loglevel)

app.debug = args.get('--debug')
print("xtas %s REST endpoint" % __version__)
if app.debug:
    print("Serving tasks:")
    pprint(list(taskq.tasks.keys()))
http_server = HTTPServer(WSGIContainer(app))
http_server.bind(args['--port'], address=args['--host']) #
http_server.start(int(args['--threads']))
IOLoop.instance().start()

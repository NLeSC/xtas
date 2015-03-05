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

import logging

from docopt import docopt

from tornado import version as tornado_version
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

app = Flask(__name__)

args = docopt(__doc__)

loglevel = logging.DEBUG if args.get('--debug') else logging.INFO
logging.basicConfig(level=loglevel)

app.debug = args.get('--debug')
print("xtas %s REST endpoint" % __version__)
if app.debug:
    print("Serving tasks:")
    pprint(list(taskq.tasks.keys()))
http_server = HTTPServer(WSGIContainer(app))
http_server.bind(args['--port'], address=args['--host'])
http_server.start(int(args['--threads']))
IOLoop.instance().start()

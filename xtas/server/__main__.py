# Server main. To run:
#   python -m xtas.server

from __future__ import print_function

from argparse import ArgumentParser
import yaml

from . import Server
from ..util import getconf


argp = ArgumentParser(description='xtas server')
argp.add_argument('--config', default='xtas.yaml', dest='config',
                  help='Path to configuration file.')
argp.add_argument('--debug', action='store_true')
args = argp.parse_args()

with open(args.config) as f:
    config = yaml.load(f)

config.setdefault('server', {})['debug'] = args.debug

server = Server(broker=getconf(config, 'main broker'),
                **config.get('server', {}))
server.run()

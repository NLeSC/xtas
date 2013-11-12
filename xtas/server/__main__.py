# Server main. To run:
#   python -m xtas.server

from __future__ import print_function

from argparse import ArgumentParser
import yaml

from . import Server


argp = ArgumentParser(description='xtas server')
argp.add_argument('--config', default='xtas.yaml', dest='config',
                  help='Path to configuration file.')
argp.add_argument('--debug', action='store_true')
argp.add_argument('--local', action='store_true',
                  help='Run tasks locally instead of distributed.')
args = argp.parse_args()

with open(args.config) as f:
    config = yaml.load(f)

config.setdefault('server', {})['debug'] = args.debug
config.setdefault('server', {})['local'] = args.local

server = Server(config)
server.run()

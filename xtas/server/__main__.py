# Server main. To run:
#   python -m xtas.server

from __future__ import print_function

from argparse import ArgumentParser

from . import Server


argp = ArgumentParser(description='xtas server')
argp.add_argument('--debug', action='store_true')

args = argp.parse_args()

server = Server(debug=args.debug)
server.run()

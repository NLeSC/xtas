from __future__ import print_function
from argparse import ArgumentParser
from os.path import dirname, exists, join
from shutil import copyfileobj
import sys

template = join(dirname(__file__), "template.yaml")

argp = ArgumentParser(description='xtas configuration generator',
                      prog='xtas.configure')
argp.add_argument('--output', '-o', default=None, dest='path',
                  help='Where to write configuration (default is stdout)')
args = argp.parse_args()

if args.path is None:
    output = sys.stdout
else:
    # XXX minor race condition up ahead; Python 3.3 has an 'x' flag for this
    if exists(args.path):
        print("xtas.configure: not overwriting {}".format(args.path),
              file=sys.stderr)
        sys.exit(1)

    output = open(args.path, "w")

try:
    with open(template) as f:
        copyfileobj(f, output)
finally:
    output.close()

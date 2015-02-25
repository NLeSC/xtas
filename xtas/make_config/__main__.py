"""Generate xtas configuration file.

Usage:
  make_config [-o file]

Options:
  -h, --help  show this help message and exit
  -o file     Write output to <file> [default: xtas_config.py].
"""

from os.path import abspath, dirname, join
from shutil import copyfileobj
import sys

from docopt import docopt


if __name__ == '__main__':
    args = docopt(__doc__)

    with open(join(dirname(__file__), '..', '_defaultconfig.py')) as default:
        print("Generating configuration file at %r" % args['-o'])
        # XXX in Python 3, we can make this safer by opening with 'x'
        with open(args['-o'], 'w') as out:
            copyfileobj(default, out)

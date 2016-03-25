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

"""Generate xtas configuration file.

Usage:
  make_config [-o file]

Options:
  -h, --help  show this help message and exit
  -o file     Write output to <file> [default: xtas_config.py].
"""

from os.path import dirname, exists, join
from shutil import copyfileobj
import sys

from docopt import docopt


def _get_default_config():
    return open(join(dirname(__file__), '_defaultconfig.py'))


if __name__ == '__main__':
    args = docopt(__doc__)

    outpath = args['-o']
    # In Python 3, we could make this safer by opening with 'x'.
    if exists(outpath):
        sys.exit("%s: %r already exists" % (sys.argv[0], outpath))

    with _get_default_config() as default:
        print("Generating configuration file at %r" % args['-o'])
        with open(outpath, 'w') as out:
            copyfileobj(default, out)

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

from __future__ import division
import errno
import logging
import os
import os.path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from six.moves.urllib.request import urlretrieve


logger = logging.getLogger(__name__)


def download_zip(url, name=None, check_dir=None):
    """Download and unzip zip file from url to $XTAS_DATA.

    Does nothing if $XTAS_DATA/check_dir exists.

    Parameters
    ----------
    url : string
        URL of resource.
    name : string
        Used by the logger, to display "Downloading [name]".
    check_dir : string
        Name of directory to which the resource is unzipped.
        Derived from the URL by default.
    """
    if check_dir is None:
        check_dir = os.path.basename(url)
        if check_dir.endswith('.zip'):
            check_dir = check_dir[:-4]
    if name is None:
        name = url
    home = make_data_home()
    check_dir = os.path.join(home, check_dir)

    # XXX race condition with multiple workers
    if not os.path.exists(check_dir):
        with NamedTemporaryFile() as temp:
            logger.info("Downloading %s" % name)
            urlretrieve(url, temp.name, reporthook=progress)
            with ZipFile(temp.name) as z:
                z.extractall(path=home)

    return check_dir


def make_data_home(subdir=None):
    """Make XTAS_DATA directory, and subdir inside it (if not None)."""
    path = (os.getenv("XTAS_DATA")
            or os.path.join(os.getenv("HOME"), "xtas_data"))
    if subdir is not None:
        path = os.path.join(path, subdir)

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
    return path


def progress(i, blocksize, totalsize):
    if i % 1000 == 0:
        logger.info("{:>7.2%}".format(min(i * blocksize, totalsize)
                                      / totalsize))

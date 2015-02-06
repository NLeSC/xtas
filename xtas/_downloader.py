from __future__ import division
import errno
import logging
import os
import os.path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from six.moves.urllib.request import urlretrieve


logger = logging.getLogger(__name__)


def _download_zip(url, name=None, check_dir=None):
    """Download and unzip zip file from url to $XTAS_DATA.

    Does nothing if $XTAS_DATA/check_dir exists.
    """
    if name is None:
        name = url
    home = _make_data_home()
    check_dir = os.path.join(home, check_dir)

    # XXX race condition with multiple workers
    if not os.path.exists(check_dir):
        with NamedTemporaryFile() as temp:
            logger.info("Downloading %s" % name)
            urlretrieve(url, temp.name, reporthook=_progress)
            with ZipFile(temp.name) as z:
                z.extractall(path=home)

    return check_dir


def _make_data_home(subdir=None):
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


def _progress(i, blocksize, totalsize):
    if i % 1000 == 0:
        logger.info("{:>7.2%}".format(min(i * blocksize, totalsize)
                                      / totalsize))

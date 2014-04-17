from __future__ import division
import errno
import os
import os.path
from tempfile import NamedTemporaryFile
from urllib import urlretrieve
from zipfile import ZipFile


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
        print("{:>7.2%}".format(min(i * blocksize, totalsize) / totalsize))

from __future__ import division
import errno
import os
import os.path
from tempfile import NamedTemporaryFile
from urllib import urlretrieve
from zipfile import ZipFile


_STANFORD_NER = (
    '''http://nlp.stanford.edu/software/stanford-ner-2014-01-04.zip'''
)


def _make_data_home():
    path = (os.getenv("XTAS_DATA")
            or os.path.join(os.getenv("HOME"), "xtas_data"))
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
    return path


def _progress(i, blocksize, totalsize):
    if i % 100 == 0:
        print("{:>7.2%}".format(min(i * blocksize, totalsize) / totalsize))


def download_stanford_ner():
    home = _make_data_home()
    ner_dir = os.path.join(home, 'stanford-ner-2014-01-04')

    if not os.path.exists(ner_dir):
        with NamedTemporaryFile() as temp:
            urlretrieve(_STANFORD_NER, temp.name, reporthook=_progress)
            with ZipFile(temp.name) as z:
                z.extractall(path=home)

    return ner_dir

from __future__ import division
import errno
import os
import os.path
import tarfile
from tempfile import NamedTemporaryFile
from urllib import urlretrieve
from zipfile import ZipFile


_MOVIE_REVIEWS = (
    'http://www.cs.cornell.edu/people/pabo/movie-review-data'
    '/review_polarity.tar.gz'
)


_STANFORD_NER = (
    '''http://nlp.stanford.edu/software/stanford-ner-2014-01-04.zip'''
)


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
    if i % 100 == 0:
        print("{:>7.2%}".format(min(i * blocksize, totalsize) / totalsize))


def download_movie_reviews():
    # TODO figure out the license on this one, maybe make the user perform
    # some action.
    movie_reviews_dir = os.path.join(_make_data_home(), 'movie_reviews')

    if not os.path.exists(movie_reviews_dir):
        with NamedTemporaryFile() as temp:
            urlretrieve(_MOVIE_REVIEWS, temp.name, reporthook=_progress)
            with tarfile.open(temp.name) as tar:
                tar.extractall(path=movie_reviews_dir)

    return os.path.join(movie_reviews_dir, 'txt_sentoken')


def download_stanford_ner():
    home = _make_data_home()
    ner_dir = os.path.join(home, 'stanford-ner-2014-01-04')

    if not os.path.exists(ner_dir):
        with NamedTemporaryFile() as temp:
            urlretrieve(_STANFORD_NER, temp.name, reporthook=_progress)
            with ZipFile(temp.name) as z:
                z.extractall(path=home)

    return ner_dir

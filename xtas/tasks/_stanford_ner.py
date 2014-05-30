from __future__ import absolute_import, print_function
from itertools import groupby
import logging
import operator
import os
import os.path
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from urllib import urlretrieve
from zipfile import ZipFile

import nltk

from .._downloader import _make_data_home, _progress


logger = logging.getLogger(__name__)


STANFORD_NER = (
    '''http://nlp.stanford.edu/software/stanford-ner-2014-01-04.zip'''
)


def download():
    home = _make_data_home()
    ner_dir = os.path.join(home, 'stanford-ner-2014-01-04')

    if not os.path.exists(ner_dir):
        with NamedTemporaryFile() as temp:
            logger.info('Downloading %s' % STANFORD_NER)
            urlretrieve(STANFORD_NER, temp.name, reporthook=_progress)
            with ZipFile(temp.name) as z:
                z.extractall(path=home)

    return ner_dir


# Download and start server at import, not call time. Import is done lazily.
ner_dir = download()
jar = os.path.join(ner_dir, 'stanford-ner.jar')
model = os.path.join(ner_dir,
                     'classifiers/english.all.3class.distsim.crf.ser.gz')
classpath = '%s:%s' % (jar, os.path.dirname(__file__))
server = Popen(['java', '-mx1000m', '-cp', classpath, 'NERServer', model],
               stdin=PIPE, stdout=PIPE)


def tag(doc, format):
    if format not in ["tokens", "names"]:
        raise ValueError("unknown format %r" % format)

    # If the doc contains unicode characters, a UnicodeEncodeError was thrown
    # in s.sendall(text). E.g. presumably the euro-sign:
    # UnicodeEncodeError: 'ascii' codec can't encode character u'\u20ac' in
    # position 460: ordinal not in range(128)

    # nltk.word_tokenize(doc) returns a list [u'xyz', ..]. Using ' '.join()
    # results in the above error. Encoding each list item first fixes the
    # problem.

    toks = nltk.word_tokenize(doc)
    text = ' '.join(t.encode('utf-8') for t in toks)

    server.stdin.write(text)
    server.stdin.write('\n')

    tagged = [token.rsplit('/', 1)
              for token in server.stdout.readline().split()]

    if format == "tokens":
        return tagged
    elif format == "names":
        return [(' '.join(token for token, _ in tokens), cls)
                for cls, tokens in groupby(tagged, operator.itemgetter(1))
                if cls != 'O']

from __future__ import absolute_import, print_function
from itertools import groupby
import logging
import operator
import os
import os.path
from subprocess import Popen, PIPE

import nltk

from .._downloader import _download_zip


logger = logging.getLogger(__name__)


STANFORD_NER = (
    '''http://nlp.stanford.edu/software/stanford-ner-2014-01-04.zip'''
)


# Download and start server at import, not call time. Import is done lazily.
ner_dir = _download_zip(STANFORD_NER, name="Stanford NER",
                        check_dir="stanford-ner-2014-01-04")
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

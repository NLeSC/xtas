from __future__ import absolute_import, print_function
import atexit
from itertools import groupby
import logging
import operator
import os
import os.path
import socket
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from time import sleep
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


# XXX the port number is completely arbitrary.
# Also, let's hope it's not available to the outside. Stanford doesn't seem to
# document this.
def start_server(port=9155):
    global ner_dir
    jar = os.path.join(ner_dir, 'stanford-ner.jar')
    model = os.path.join(ner_dir,
                         'classifiers/english.all.3class.distsim.crf.ser.gz')

    print("Starting Stanford NER on port %d" % port)
    server = Popen(['java', '-mx1000m', '-cp', jar,
                    'edu.stanford.nlp.ie.NERServer',
                    '-outputFormat', 'slashTags',
                    '-loadClassifier', model,
                    '-port', str(port)],
                   stderr=PIPE)

    def kill(p):
        p.terminate()
        sleep(2)
        p.kill()
        p.wait()

    atexit.register(kill, server)

    stderr = server.stderr.readline()
    print(stderr, end='')
    if not 'done' in stderr:
        raise ValueError('cannot start Stanford NER')

    # When Stanford NER reports ready to serve requests, it's not actually
    # ready.
    sleep(1)

    return server, port


# Download and start server at import, not call time. Import is done lazily.
ner_dir = download()
server, port = start_server()


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

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))
    s.sendall(text)
    s.send('\n')
    tagged = [token.rsplit('/', 1) for token in s.recv(10 * len(text)).split()]

    if format == "tokens":
        return tagged
    elif format == "names":
        return [(' '.join(token for token, _ in tokens), cls)
                for cls, tokens in groupby(tagged, operator.itemgetter(1))
                if cls != 'O']

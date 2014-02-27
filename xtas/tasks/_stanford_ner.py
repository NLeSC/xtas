from __future__ import absolute_import
import os
import os.path
from tempfile import NamedTemporaryFile
from urllib import urlretrieve
from zipfile import ZipFile

import nltk
from nltk.tag.stanford import NERTagger

from .._downloader import _make_data_home, _progress


STANFORD_NER = (
    '''http://nlp.stanford.edu/software/stanford-ner-2014-01-04.zip'''
)


def download():
    home = _make_data_home()
    ner_dir = os.path.join(home, 'stanford-ner-2014-01-04')

    if not os.path.exists(ner_dir):
        with NamedTemporaryFile() as temp:
            urlretrieve(STANFORD_NER, temp.name, reporthook=_progress)
            with ZipFile(temp.name) as z:
                z.extractall(path=home)

    return ner_dir


# Download at import, not call time. Import will be done lazily.
nltk.download('punkt', quiet=False)
ner_dir = download()


# XXX This is really slow. Maybe speed it up by pre-forking JVMs?
def tag(doc, model):
    sentences = (nltk.word_tokenize(s) for s in nltk.sent_tokenize(doc))

    tagger = NERTagger(os.path.join(ner_dir, model),
                       os.path.join(ner_dir, 'stanford-ner.jar'))
    return tagger.batch_tag(sentences)

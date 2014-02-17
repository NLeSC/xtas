"""Embarrasingly parallel (per-document) tasks."""

from __future__ import absolute_import

import json
import os
from urllib import urlencode
from urllib2 import urlopen

import nltk

from .es import fetch
from ..celery import app
from ..downloader import download_stanford_ner


@app.task
def morphy(doc):
    """Lemmatize tokens using morphy, WordNet's lemmatizer."""
    # XXX Results will be better if we do POS tagging first, but then we
    # need to map Penn Treebank tags to WordNet tags.
    nltk.download('wordnet', quiet=False)
    return map(nltk.WordNetLemmatizer().lemmatize,
               _tokenize_if_needed(fetch(doc)))


def _tokenize_if_needed(s):
    if isinstance(s, basestring):
        # XXX building token dictionaries is actually wasteful...
        return [tok['token'] for tok in tokenize(s)]
    return s


_STANFORD_DEFAULT_MODEL = \
    'classifiers/english.all.3class.distsim.crf.ser.gz'


@app.task
def stanford_ner_tag(doc, model=_STANFORD_DEFAULT_MODEL):
    """Named entity recognizer using Stanford NER.

    Parameters
    ----------
    doc : document

    model : str, optional
        Name of model file for Stanford NER tagger, relative to Stanford NER
        installation directory.

    Returns
    -------
    tagged : list of list of pair of string
        For each sentence, a list of (word, tag) pairs.
    """
    import nltk
    from nltk.tag.stanford import NERTagger

    nltk.download('punkt', quiet=False)
    ner_dir = download_stanford_ner()

    doc = fetch(doc)
    sentences = (_tokenize_if_needed(s) for s in nltk.sent_tokenize(doc))

    tagger = NERTagger(os.path.join(ner_dir, model),
                       os.path.join(ner_dir, 'stanford-ner.jar'))
    return tagger.batch_tag(sentences)


@app.task
def pos_tag(tokens, model):
    if model != 'nltk':
        raise ValueError("unknown POS tagger %r" % model)
    return nltk.pos_tag([t["token"] for t in tokens])


@app.task
def tokenize(doc):
    text = fetch(doc)
    return [{"token": t} for t in nltk.word_tokenize(text)]


@app.task
def semanticize(doc):
    text = fetch(doc)

    lang = 'nl'
    if not lang.isalpha():
        raise ValueError("not a valid language: %r" % lang)
    url = 'http://semanticize.uva.nl/api/%s?%s' % (lang,
                                                   urlencode({'text': text}))
    return json.loads(urlopen(url).read())['links']


@app.task
def untokenize(tokens):
    return ' '.join(tokens)

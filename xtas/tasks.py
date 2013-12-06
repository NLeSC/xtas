from __future__ import absolute_import

import json
import nltk
from rawes import Elastic
from urllib import urlencode
from urllib2 import urlopen

from xtas.celery import app

es = Elastic()


@app.task
def fetch_es(idx, typ, id, field):
    """Get a single document from Elasticsearch."""
    return es[idx][typ][id].get()['_source'][field]


@app.task
def morphy(tokens):
    """Lemmatize tokens using morphy, WordNet's lemmatizer"""

    lemmatize = nltk.WordNetLemmatizer().lemmatize
    for t in tokens:
        tok = t["token"]
        # XXX WordNet POS tags don't align with Penn Treebank ones
        pos = t.get("pos")
        try:
            t["lemma"] = lemmatize(tok, pos)
        except KeyError:
            # raised for an unknown part of speech tag
            pass

    return tokens


@app.task
def pos_tag(tokens, model):
    if model != 'nltk':
        raise ValueError("unknown POS tagger %r" % model)
    return nltk.pos_tag([t["token"] for t in tokens])


@app.task
def store_es(data, taskname, idx, typ, id):
    # XXX there's a way to do this using _update and POST, but I can't get it
    # to work with rawes.
    handle = es[idx][typ][id]
    doc = handle.get()
    doc.setdefault('xtas-result', {})[taskname] = data
    handle.put(data=doc)

    return data


@app.task
def tokenize(text):
    return [{"token": t} for t in nltk.word_tokenize(text)]


@app.task
def semanticize(lang, text):
    if not lang.isalpha():
        raise ValueError("not a valid language: %r" % lang)
    url = 'http://semanticize.uva.nl/api/%s?%s' % (lang,
                                                   urlencode({'text': text}))
    return json.loads(urlopen(url).read())['links']


@app.task
def untokenize(tokens):
    return ' '.join(tokens)

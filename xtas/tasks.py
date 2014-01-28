from __future__ import absolute_import

from datetime import datetime
import json
from urllib import urlencode
from urllib2 import urlopen

import nltk
from rawes import Elastic

from xtas.celery import app

es = Elastic()


class ESDocument(object):
    """Handle on a document living in the ES store."""

    def __init__(self, idx, typ, id):
        self.index = idx
        self.type = typ
        self.id = id

    def fetch(self):
        return es[self.index][self.type][self.id].get()['_source'][field]


def fetch(doc):
    """Fetch document (if necessary). Returns strings as-is."""
    if hasattr(doc, "fetch"):
        doc = doc.fetch()
    return doc


@app.task
def fetch_query_batch(idx, typ, query, field):
    """Fetch all documents matching query and return them as a list.

    Returns a list of field contents, with documents that don't have the
    required field silently filtered out.
    """
    r = es[idx][typ]._search.get(data={'query': query})
    r = (hit['_source'].get('body', None) for hit in r['hits']['hits'])
    return [hit for hit in r if hit is not None]


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


def _tokenize_if_needed(s):
    if isinstance(s, basestr):
        return tokenize(s)
    return s


_STANFORD_DEFAULT_MODEL = \
    'stanford-ner-2014-01-04/classifiers/english.all.3class.distsim.crf.ser.gz'
_STANFORD_DEFAULT_JAR = \
    'stanford-ner-2014-01-04/stanford-ner.jar'

@app.task
def stanford_ner_tag(sentences, model=None, jar=None):
    """Named entity recognizer using Stanford NER.

    Parameters
    ----------
    sentences : iterable over {str, sequence of str}
        Input sentences, either as strings or sequences of words. Strings
        will be tokenized with a default tokenizer.

    model : str, optional
        Path to model file for Stanford NER tagger.

    jar : str, optional
        Path to JAR file of Stanford NER tagger.

    Returns
    -------
    tagged : list of list of pair of string
        For each sentence, a list of (word, tag) pairs.
    """
    # TODO introduce config file that can hold these paths.

    from nltk.tag.stanford import NERTagger

    if model is None:
        model = _STANFORD_DEFAULT_MODEL
    if jar is None:
        jar = _STANFORD_DEFAULT_JAR

    sentences = map(_tokenize_if_needed, sentences)

    tagger = NERTagger(model, jar)
    return tagger.batch_tag(sentences)


@app.task
def pos_tag(tokens, model):
    if model != 'nltk':
        raise ValueError("unknown POS tagger %r" % model)
    return nltk.pos_tag([t["token"] for t in tokens])


@app.task
def store_single(data, taskname, idx, typ, id):
    # XXX there's a way to do this using _update and POST, but I can't get it
    # to work with rawes.
    handle = es[idx][typ][id]
    doc = handle.get()['_source']

    results = doc.setdefault('xtas_results', {})
    results[taskname] = {}
    results[taskname]['data'] = data
    results[taskname]['timestamp'] = datetime.now().isoformat()

    handle.put(data=doc)

    return data


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


# Batch tasks.

@app.task
def kmeans(docs, k, lsa=None):
    """Run k-means clustering on a vectorized set of documents.

    Parameters
    ----------
    k : integer
        Number of clusters.
    docs : list of strings
        Untokenized documents.
    lsa : integer, optional
        Whether to perform latent semantic analysis before k-means, and if so,
        with how many components/topics.

    Returns
    -------
    labels : list of integers
        Cluster labels (integers in the range [0..k)) for all documents in X.
    """
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import Normalizer

    if lsa is not None:
        kmeans = make_pipeline(TfidfVectorizer(min_df=2),
                               TruncatedSVD(n_components=lsa),
                               Normalizer(),
                               MiniBatchKMeans(n_clusters=k))
    else:
        kmeans = make_pipeline(TfidfVectorizer(min_df=2),
                               MiniBatchKMeans(n_clusters=k))

    # XXX return friendlier output?
    return kmeans.fit(docs).steps[-1][1].labels_.tolist()


@app.task
def parsimonious_wordcloud(docs, w=.5, k=10):
    from weighwords import ParsimoniousLM

    model = ParsimoniousLM(docs, w=w)
    return [model.top(10, d) for d in docs]

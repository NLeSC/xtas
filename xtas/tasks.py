from __future__ import absolute_import

from datetime import datetime
import json
import os
from urllib import urlencode
from urllib2 import urlopen

import nltk
from rawes import Elastic

from xtas.celery import app
from xtas.downloader import download_stanford_ner
from xtas.utils import batches

es = Elastic()


_ES_DOC_FIELDS = ('index', 'type', 'id', 'field')

def es_document(idx, typ, id, field):
    """Returns a handle on a document living in the ES store.

    Returns a dict instead of a custom object to ensure JSON serialization
    works.
    """
    return {'index': idx, 'type': typ, 'id': id, 'field': field}


def fetch(doc):
    """Fetch document (if necessary).

    Parameters
    ----------
    doc : {dict, string}
        A dictionary representing a handle returned by es_document, or a plain
        string.
    """
    if isinstance(doc, dict) and set(doc.keys()) == set(_ES_DOC_FIELDS):
        idx, typ, id, field = [doc[k] for k in _ES_DOC_FIELDS]
        return es[idx][typ][id].get()['_source'][field]
    else:
        # Assume simple string
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
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import Normalizer

    if lsa is not None:
        kmeans = Pipeline([('tfidf', TfidfVectorizer(min_df=2)),
                           ('lsa', TruncatedSVD(n_components=lsa)),
                           ('l2norm', Normalizer()),
                           ('kmeans', MiniBatchKMeans(n_clusters=k))])
    else:
        kmeans = Pipeline([('tfidf', TfidfVectorizer(min_df=2)),
                           ('kmeans', MiniBatchKMeans(n_clusters=k))])

    # XXX return friendlier output?
    return kmeans.fit(docs).steps[-1][1].labels_.tolist()


@app.task
def big_kmeans(docs, k, batch_size=1000, n_features=(2 ** 20),
               single_pass=True):
    """k-means for very large sets of documents.

    """
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.feature_extraction.text import HashingVectorizer

    v = HashingVectorizer(input="content", n_features=n_features, norm="l2")
    km = MiniBatchKMeans(n_clusters=k)

    labels = []
    for batch in batches(docs, batch_size):
        batch = map(fetch, docs)
        batch = v.transform(batch)
        y = km.fit_predict(batch)
        if single_pass:
            labels.extend(y.tolist())

    if not single_pass:
        for batch in batches(docs, batch_size):
            batch = map(fetch, docs)
            batch = v.transform(batch)
            labels.extend(km.predict(batch).tolist())

    return labels


@app.task
def parsimonious_wordcloud(docs, w=.5, k=10):
    from weighwords import ParsimoniousLM

    model = ParsimoniousLM(docs, w=w)
    return [model.top(10, d) for d in docs]

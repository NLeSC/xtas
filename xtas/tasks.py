from __future__ import absolute_import

from datetime import datetime
import json
from urllib import urlencode
from urllib2 import urlopen

import nltk
from rawes import Elastic

from xtas.celery import app

es = Elastic()


@app.task
def fetch_single(idx, typ, id, field):
    """Get a single document from Elasticsearch."""
    return es[idx][typ][id].get()['_source'][field]


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
    doc = handle.get()['_source']

    results = doc.setdefault('xtas_results', {})
    results[taskname] = {}
    results[taskname]['data'] = data
    results[taskname]['timestamp'] = datetime.now().isoformat()

    handle.put(data=doc)

    return data


@app.task
def tokenize(text):
    return [{"token": t} for t in nltk.word_tokenize(text)]


@app.task
def semanticize(text):
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

    if lsa is not None:
        kmeans = make_pipeline(TfidfVectorizer(min_df=2),
                               TruncatedSVD(n_components=lsa),
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

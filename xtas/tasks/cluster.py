"""Clustering and topic modelling tasks.

These tasks process batches of documents, denoted as lists of strings.
"""

from __future__ import absolute_import

import operator

import cytoolz as toolz
from six import itervalues

from .es import fetch
from ..core import app
from .._utils import tosequence


def _vectorizer(**kwargs):
    """Construct a TfidfVectorizer with sane settings."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    if 'min_df' not in kwargs:
        kwargs['min_df'] = 2
    if 'sublinear_tf' not in kwargs:
        kwargs['sublinear_tf'] = True

    kwargs['input'] = 'content'

    return TfidfVectorizer(**kwargs)


def group_clusters(docs, labels):
    """Group docs by their cluster labels."""
    return [zip(*cluster)[1]
            for cluster in itervalues(toolz.groupby(operator.itemgetter(0),
                                                    zip(labels, docs)))]


@app.task
def kmeans(docs, k, lsa=None):
    """Run k-means clustering on a set of documents.

    Uses scikit-learn to tokenize documents, compute tf-idf weights, perform
    (optional) LSA transformation, and cluster.

    Parameters
    ----------
    docs : list of strings
        Untokenized documents.
    k : integer
        Number of clusters.
    lsa : integer, optional
        Whether to perform latent semantic analysis before k-means, and if so,
        with how many components/topics.

    Returns
    -------
    clusters : sequence of sequence of documents
        The input documents, grouped by cluster. The order of clusters and
        the order of documents within clusters is unspecified.
    """
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.decomposition import TruncatedSVD
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import Normalizer

    docs = tosequence(docs)

    if lsa is not None:
        kmeans = make_pipeline(_vectorizer(),
                               TruncatedSVD(n_components=lsa),
                               Normalizer(),
                               MiniBatchKMeans(n_clusters=k))
    else:
        kmeans = make_pipeline(_vectorizer(),
                               MiniBatchKMeans(n_clusters=k))

    labels = kmeans.fit(fetch(d) for d in docs).steps[-1][1].labels_
    return group_clusters(docs, labels)


@app.task
def big_kmeans(docs, k, batch_size=1000, n_features=(2 ** 20),
               single_pass=True):
    """k-means for very large sets of documents.

    See kmeans for documentation. Differs from that function in that it does
    not computer tf-idf or LSA, and fetches the documents in a streaming
    fashion, so they don't need to be held in memory. It does not do random
    restarts.

    If the option single_pass is set to False, the documents are visited
    twice: once to fit a k-means model, once to determine their label in
    this model.
    """
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.feature_extraction.text import HashingVectorizer

    docs = tosequence(docs)

    v = HashingVectorizer(input="content", n_features=n_features, norm="l2")
    km = MiniBatchKMeans(n_clusters=k)

    labels = []
    for batch in toolz.partition_all(batch_size, docs):
        batch = map(fetch, docs)
        batch = v.transform(batch)
        y = km.fit_predict(batch)
        if single_pass:
            labels.extend(y.tolist())

    if not single_pass:
        for batch in toolz.partition_all(batch_size, docs):
            batch = map(fetch, docs)
            batch = v.transform(batch)
            labels.extend(km.predict(batch).tolist())

    return group_clusters(docs, labels)


@app.task
def lsa(docs, k, random_state=None):
    """Latent semantic analysis.

    Parameters
    ----------
    docs : list of strings
        Untokenized documents.
    k : integer
        Number of topics.
    random_state : integer, optional
        Random number seed, for reproducibility of results.

    Returns
    -------
    model : list of list of (string, float)
        The k components of the LSA model, represented as lists of
        (term, weight) pairs.
    """
    from sklearn.decomposition import TruncatedSVD
    from sklearn.pipeline import make_pipeline

    vect = _vectorizer()
    svd = TruncatedSVD(n_components=k)
    pipe = make_pipeline(vect, svd).fit(docs)

    vocab = vect.vocabulary_
    return [zip(vocab, comp) for comp in svd.components_]


@app.task
def lda(docs, k):
    """Latent Dirichlet allocation topic model.

    Uses Gensim's LdaModel after tokenizing using scikit-learn's
    TfidfVectorizer.

    Parameters
    ----------
    k : integer
        Number of topics.
    """
    from gensim.matutils import Sparse2Corpus
    from gensim.models import LdaModel

    # Use a scikit-learn vectorizer rather than Gensim's equivalent
    # for speed and consistency with LSA and k-means.
    vect = _vectorizer()
    corpus = vect.fit_transform(fetch(d) for d in docs)
    corpus = Sparse2Corpus(corpus)

    model = LdaModel(corpus=corpus, num_topics=k)

    topics = model.show_topics(formatted=False)
    vocab = vect.get_feature_names()
    #return [(vocab[int(idx)], w) for topic in topics for w, idx in topic]
    return [[(vocab[int(idx)], w) for w, idx in topic] for topic in topics]


@app.task
def parsimonious_wordcloud(docs, w=.5, k=10):
    """Fit a parsimonious language model to terms in docs."""
    from weighwords import ParsimoniousLM

    model = ParsimoniousLM(docs, w=w)
    return [model.top(k, d) for d in docs]

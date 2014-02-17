"""Clustering and topic modelling tasks."""

from __future__ import absolute_import

from .es import fetch
from ..celery import app
from ..utils import batches


def _vectorizer(**kwargs):
    """Construct a TfidfVectorizer with sane settings."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    if 'min_df' not in kwargs:
        kwargs['min_df'] = 2
    if 'sublinear_tf' not in kwargs:
        kwargs['sublinear_tf'] = True

    kwargs['input'] = 'content'

    return TfidfVectorizer(**kwargs)


@app.task
def kmeans(docs, k, lsa=None):
    """Run k-means clustering on a vectorized set of documents.

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
    labels : list of integers
        Cluster labels (integers in the range [0..k)) for all documents in X.
    """
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.decomposition import TruncatedSVD
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import Normalizer

    if lsa is not None:
        kmeans = Pipeline([('tfidf', _vectorizer()),
                           ('lsa', TruncatedSVD(n_components=lsa)),
                           ('l2norm', Normalizer()),
                           ('kmeans', MiniBatchKMeans(n_clusters=k))])
    else:
        kmeans = Pipeline([('tfidf', _vectorizer()),
                           ('kmeans', MiniBatchKMeans(n_clusters=k))])

    # XXX return friendlier output?
    return kmeans.fit(fetch(d) for d in docs).steps[-1][1].labels_.tolist()


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
def lsa(docs, k, random_state=None):
    """Latent semantic analysis.

    Parameters
    ----------
    docs : list of strings
        Untokenized documents.
    k : integer
        Number of topics.
    random_state : integer, optional
        Random number seed, for reproducibility.

    Returns
    -------
    model : list of list of (string, float)
        The k components of the LSA model, represented as lists of
        (term, weight) pairs.
    """
    from sklearn.decomposition import TruncatedSVD
    from sklearn.pipeline import Pipeline

    vect = _vectorizer()
    svd = TruncatedSVD(n_components=k)
    pipe = Pipeline([('tfidf', vect), ('svd', svd)])
    pipe.fit(docs)

    vocab = vect.vocabulary_
    return [zip(vocab, comp) for comp in svd.components_]


@app.task
def lda(docs, k):
    """Latent Dirichlet allocation using Gensim.

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
    from weighwords import ParsimoniousLM

    model = ParsimoniousLM(docs, w=w)
    return [model.top(10, d) for d in docs]

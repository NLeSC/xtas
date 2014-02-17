"""Clustering and topic modelling tasks."""

from __future__ import absolute_import

from .es import fetch
from ..celery import app
from ..utils import batches


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

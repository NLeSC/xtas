# Copyright 2013-2015 Netherlands eScience Center and University of Amsterdam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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


def _group_clusters(docs, labels):
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
    return _group_clusters(docs, labels)


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

    vectorizer = HashingVectorizer(input="content",
                                   n_features=n_features, norm="l2")
    kmeans = MiniBatchKMeans(n_clusters=k)

    labels = []
    for batch in toolz.partition_all(batch_size, docs):
        batch = map(fetch, batch)
        batch = vectorizer.transform(batch)
        y = kmeans.fit_predict(batch)
        if single_pass:
            labels.extend(y.tolist())

    if not single_pass:
        for batch in toolz.partition_all(batch_size, docs):
            batch = map(fetch, batch)
            batch = vectorizer.transform(batch)
            labels.extend(kmeans.predict(batch).tolist())

    return _group_clusters(docs, labels)


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
def lda(docs, k, random_state=None):
    """Latent Dirichlet allocation topic model.

    Uses scikit-learn's TfidfVectorizer and LatentDirichletAllocation.

    Parameters
    ----------
    k : integer
        Number of topics.
    """
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.pipeline import make_pipeline

    vect = _vectorizer()
    lda = LatentDirichletAllocation(n_topics=k, random_state=random_state)
    pipe = make_pipeline(vect, lda).fit(docs)

    vocab = vect.vocabulary_
    # XXX it looks like scikit-learn's LDA holds unnormalized probabilities
    # (see also https://github.com/scikit-learn/scikit-learn/issues/6320).
    # We simply normalize to get rid of the issue.
    return [zip(vocab, comp / comp.sum()) for comp in lda.components_]


@app.task
def parsimonious_wordcloud(docs, w=.5, k=10):
    """Fit parsimonious language models to docs.

    A parsimonious language model shows which words "stand out" in each
    document when compared to the full set. These words are the ones you
    might want to display in a word cloud.

    This function fits a background model to all of docs, then fits individual
    models to each document in turn using the background model.

    Parameters
    ----------
    docs : list
        List of documents.

    w : float
        Weight assigned to the document terms when fitting individual models,
        relative to the background model. Should be a number between 0
        (background model only) and 1 (background model disabled).

    k : integer
        Number of terms to return per document.

    Returns
    -------
    terms : list of list of (string, float)
        For each document in docs, a top-k list of most probable words and
        their log-probabilities.
    """
    from ._weighwords import ParsimoniousLM

    model = ParsimoniousLM(docs, w=w)
    return [model.top(k, d) for d in docs]

# Tests for batch operations.
from unittest import SkipTest

from nose.tools import assert_equal

from xtas.tasks.cluster import (big_kmeans, kmeans, lda, lsa,
                                parsimonious_wordcloud)


# The clusters in these should be obvious.
DOCS = [
    "apple pear banana fruit",
    "apple apple cherry banana",
    "pear fruit banana pineapple",
    "beer pizza pizza beer",
    "pizza pineapple coke",
    "beer coke sugar"
]


def test_kmeans():
    try:
        import sklearn
    except ImportError:
        raise SkipTest("Module sklearn not installed, skipping kmeans test")
    clusters = kmeans.s(2).delay(DOCS).get()
    assert_equal(len(clusters), len(DOCS))
    assert_equal(set([0, 1]), set(clusters))

    clusters = big_kmeans.s(2).delay(DOCS).get()
    assert_equal(len(clusters), len(DOCS))
    assert_equal(set([0, 1]), set(clusters))


def test_topic_models():
    try:
        import gensim
        import sklearn
    except ImportError:
        raise SkipTest("Need Gensim and scikit-learn for topic models.")

    n_topics = 3
    for estimator in [lda]:
        topics = estimator.s(n_topics).delay(DOCS).get()
        assert_equal(len(topics), n_topics)
        assert_equal(set(term for term, _ in topics[0]),
                     set(term for term, _ in topics[1]))


def test_wordcloud():
    try:
        import weighwords
    except ImportError:
        raise SkipTest("Module weightwords not installed,"
                       " skipping wordcloud test")
    cloud = parsimonious_wordcloud([doc.split() for doc in DOCS])
    assert_equal(len(cloud), len(DOCS))
    assert_equal(len(cloud[0]), 10)

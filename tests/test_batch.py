# Tests for batch operations.
from unittest import SkipTest

from nose.tools import assert_equal, assert_not_equal

from celery import chain
from xtas.tasks import big_kmeans, kmeans, parsimonious_wordcloud

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


def test_wordcloud():
    try:
        import weighwords
    except ImportError:
        raise SkipTest("Module weightwords not installed, skipping wordcloud test")
    cloud = parsimonious_wordcloud([doc.split() for doc in DOCS])
    assert_equal(len(cloud), len(DOCS))
    assert_equal(len(cloud[0]), 10)

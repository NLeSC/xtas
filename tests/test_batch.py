# Tests for batch operations.

from nose.tools import assert_equal, assert_not_equal

from celery import chain
from xtas.tasks import kmeans, parsimonious_wordcloud

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
    clusters = kmeans.s(2).delay(DOCS).get()
    assert_equal(len(set(clusters[:3])), 1)
    assert_equal(len(set(clusters[3:])), 1)
    assert_not_equal(clusters[0], clusters[-1])


def test_wordcloud():
    cloud = parsimonious_wordcloud([doc.split() for doc in DOCS])
    assert_equal(len(cloud), len(DOCS))
    assert_equal(len(cloud[0]), 10)

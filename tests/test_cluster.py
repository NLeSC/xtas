from celery import chain
from xtas.tasks import kmeans

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

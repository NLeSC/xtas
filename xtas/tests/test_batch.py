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

# Tests for batch operations.
from nose.tools import assert_equal

from xtas.tasks.cluster import (big_kmeans, kmeans, lda, lsa,
                                parsimonious_wordcloud)


# The clusters in these should be obvious.
DOCS = sorted([
    "apple pear banana fruit",
    "apple apple cherry banana",
    "pear fruit banana pineapple",
    "beer pizza pizza beer",
    "pizza pineapple coke",
    "beer coke sugar"
])


def test_kmeans():
    clusters = kmeans.s(2).delay(DOCS).get()
    assert_equal(len(clusters), 2)
    assert_equal(DOCS, sorted(clusters[0] + clusters[1]))

    clusters = big_kmeans.s(3).delay(DOCS).get()
    assert_equal(len(clusters), 3)
    assert_equal(DOCS, sorted(clusters[0] + clusters[1] + clusters[2]))


def test_topic_models():
    n_topics = 3
    for estimator in [lda, lsa]:
        topics = estimator.s(n_topics).delay(DOCS).get()
        assert_equal(len(topics), n_topics)
        assert_equal(set(term for term, _ in topics[0]),
                     set(term for term, _ in topics[1]))


def test_wordcloud():
    cloud = parsimonious_wordcloud([doc.split() for doc in DOCS])
    assert_equal(len(cloud), len(DOCS))
    assert_equal(len(cloud[0]), 10)

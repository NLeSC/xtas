from nose.tools import assert_equal, assert_less, assert_true
from unittest import skip, SkipTest

from xtas.tasks import movie_review_polarity, stanford_ner_tag, tokenize


def test_movie_review_polarity():
    try:
        import sklearn
    except ImportError:
        raise SkipTest("movie review classifier requires scikit-learn")

    # <.5 == probably not positive.
    assert_less(movie_review_polarity("This movie sucks."), .5)


def test_tokenize():
    tokens = tokenize("My hovercraft is full of eels.")
    expected = "My hovercraft is full of eels .".split()
    for obs, exp in zip(tokens, expected):
        assert_equal(obs, {"token": exp})


@skip
def test_stanford_ner():
    # From Wikipedia front page, 10 Feb 2014.
    ne = stanford_ner_tag("Academy Award-winning actor Philip Seymour Hoffman"
                          " dies at the age of 46.")
    [sentence] = ne
    for token, tag in sentence:
        assert_true(isinstance(token, basestring))
        assert_true(tag in ["O", "PERSON"])

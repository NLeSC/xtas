import numbers

from nose.tools import assert_equal, assert_true

from xtas.tasks.cluster import parsimonious_wordcloud


def test_parsimonious_wordcloud():
    docs = map(lambda s: s.split(),
               ["an apple a day keeps the doctor away",
                "orange is the new black",
                "comparing apples and oranges"])
    lm = parsimonious_wordcloud(docs, k=4)
    assert_equal(3, len(lm))
    for x in lm:
        assert_equal(4, len(x))
        for term, weight in x:
            assert_true(isinstance(term, basestring))
            assert_true(isinstance(weight, numbers.Real))

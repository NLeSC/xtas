# coding: utf-8

from nose.tools import assert_equal, assert_in, assert_less, assert_true

from xtas.tasks import (guess_language, morphy, movie_review_polarity,
                        stanford_ner_tag, sentiwords_tag, tokenize)


def test_langid():
    # langid thinks "Hello, world!" is Dutch, hence the Joyce.
    lang, prob = guess_language("Three quarks for muster Mark")
    assert_equal(lang, "en")
    assert_true(isinstance(prob, float))

    lang, prob = guess_language(u"Καλημέρα κόσμε", output="rank")[0]
    assert_equal(lang, "el")
    assert_true(isinstance(prob, float))


def test_morphy():
    s = "The cats sat on the mats."     # morphy doesn't catch sat
    lemmata = morphy(s)
    assert_equal(lemmata, "The cat sat on the mat .".split())


def test_movie_review_polarity():
    # <.5 == probably not positive.
    assert_less(movie_review_polarity("This movie sucks."), .5)


def test_sentiwords():
    bag = sentiwords_tag("I'd like a cold beer.")
    assert_true(isinstance(bag, dict))
    assert_in("like", bag)
    assert_in("beer", bag)

    tokens = sentiwords_tag("bla a fortiori the foo quuxes a priori the baz",
                            output="tokens")
    assert_equal(tokens,
                 ['bla', ('a fortiori', 0.15793), 'the', 'foo',
                  'quuxes', ('a priori', 0.02784), 'the', 'baz'])


def test_tokenize():
    tokens = tokenize("My hovercraft is full of eels.")
    expected = "My hovercraft is full of eels .".split()
    for obs, exp in zip(tokens, expected):
        assert_equal(obs, {"token": exp})


def test_stanford_ner():
    # From Wikipedia front page, 10 Feb 2014.
    phrase = ("Academy Award-winning actor Philip Seymour Hoffman"
              " dies at the age of 46.")

    ne = stanford_ner_tag(phrase)
    for token, tag in ne:
        assert_true(isinstance(token, basestring))
        assert_true(tag in ["O", "PERSON"])

    names = stanford_ner_tag(phrase, output="names")
    # Stanford doesn't pick up "Academy Award". This is not our fault.
    # (XXX divise a better test.)
    assert_equal(names, [("Philip Seymour Hoffman", "PERSON")])

# coding: utf-8

from nose.tools import assert_equal, assert_in, assert_less, assert_true, assert_greater

from xtas.tasks import (guess_language, morphy, movie_review_polarity,
                        stanford_ner_tag, sentiwords_tag, tokenize,
                        dbpedia_spotlight)


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


def test_dbpedia_spotlight():
    en_text = u"Will the efforts of artists like Moby help to preserve the Arctic?"
    nl_text = u"Ik kan me iets herrinneren over de burgemeester van Amstelveen \
               en het achterwerk van M\xe1xima. Verder was Koningsdag een zwart gat."

    en_annotations = dbpedia_spotlight(en_text, lang='en')
    nl_annotations = dbpedia_spotlight(nl_text, lang='nl')

    # Expect `Arctic` and `Moby` to be found in en_text
    assert_equal(len(en_annotations), 2)
    for ann in en_annotations:
        assert_in(ann['name'], {'Arctic', 'Moby'})
        # The disambiguation candidates should be of type list
        assert_true(isinstance(ann['resource'], list))
        # In this case, the top candidate's uri == the name
        assert_equal(ann['name'], ann['resource'][0]['uri'])

    # Expect {"burgemeester", "Amstelveen", u"M\xe1xima",
    # "Koningsdag", "zwart gat"} to be found in nl_text
    assert_equal(len(nl_annotations), 5)
    sf_set = set([ann['name'] for ann in nl_annotations])
    assert_equal(sf_set, {u"burgemeester", u"Amstelveen", u"M\xe1xima", u"Koningsdag", u"zwart gat"})
    for ann in en_annotations:
        # The disambiguation candidates should be of type list
        assert_true(isinstance(ann['resource'], list))
        # There should be at least one candidate
        assert_greater(ann['resource'], 0)

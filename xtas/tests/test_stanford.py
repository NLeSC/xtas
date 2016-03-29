# coding: utf-8

from nose.tools import assert_in, assert_true

from xtas.tasks import stanford_ner_tag


def test_stanford_ner():
    # From Wikipedia front page, 29 March 2016
    phrase = ("Benjamin Franklin Tilley was an officer in the United States"
              " Navy and the first acting governor of of what is now"
              " American Samoa")

    ne = stanford_ner_tag(phrase)
    for token, tag in ne:
        assert_true(isinstance(token, basestring))
        assert_true(tag in ["O", "PERSON", "ORGANIZATION", "LOCATION"])

    names = stanford_ner_tag(phrase, output="names")
    assert_in(("Benjamin Franklin Tilley", "PERSON"), names)
    assert_in(("United States Navy", "ORGANIZATION"), names)
    assert_in(("American Samoa", "LOCATION"), names)


def test_stanford_ner_encoding():
    # Shouldn't raise an exception. Actually more a test for fetch/chardet,
    # but detected in the context of Stanford NER, so a non-regression test.
    stanford_ner_tag('\xe9toile'.decode('latin-1'))
    stanford_ner_tag('\xe9toile')

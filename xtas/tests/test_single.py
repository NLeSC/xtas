# coding: utf-8

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

from nose.tools import (assert_equal, assert_greater, assert_in, assert_less,
                        assert_true)

from xtas.tasks import (dbpedia_spotlight, guess_language, morphy,
                        movie_review_emotions, movie_review_polarity,
                        nlner_conll, stem_snowball, sentiwords_tag, tokenize)


def test_langid():
    # langid thinks "Hello, world!" is Dutch, hence the Joyce.
    lang, prob = guess_language("Three quarks for muster Mark")
    assert_equal(lang, "en")
    assert_true(isinstance(prob, float))

    lang, prob = guess_language(u"Καλημέρα κόσμε", output="rank")[0]
    assert_equal(lang, "el")
    assert_true(isinstance(prob, float))


def test_stemmers():
    """Test morphy and snowball/Porter stemmers."""

    s_en = "The cats sat on the mats."
    out_en = "The cat sat on the mat .".split()     # "sat" is hard to stem...

    lemmata = morphy(s_en)
    assert_equal(lemmata, out_en)

    stems = stem_snowball(s_en, language='en')
    assert_equal(stems, out_en)

    stems = stem_snowball(s_en, language='porter')
    assert_equal(stems, out_en)


def test_movie_review_polarity():
    # <.5 == probably not positive.
    assert_less(movie_review_polarity("This movie sucks."), .5)


def test_sentiwords():
    bag = sentiwords_tag("Is this a good good test?")
    words = set(["is", "this", "a", "good", "test"])
    for word in bag:
        assert_in(word, words)
        score, count = bag[word]
        assert_true(score != 0)     # We don't report on neutral terms.
        assert_greater(count, 0)

    tokens = sentiwords_tag("bla a fortiori the foo quuxes a priori the baz",
                            output="tokens")
    assert_equal(tokens,
                 ['bla', ('a fortiori', 0.15793), 'the', 'foo',
                  'quuxes', ('a priori', 0.02784), 'the', 'baz'])


def test_tokenize():
    tokens = tokenize("My hovercraft is full of eels.")
    expected = "My hovercraft is full of eels .".split()
    assert_equal(tokens, expected)


def test_dbpedia_spotlight():
    en_text = (u"Will the efforts of artists like Moby"
               u" help to preserve the Arctic?")
    nl_text = (u"Ik kan me iets herrinneren over de burgemeester van"
               u" Amstelveen en het achterwerk van M\xe1xima."
               u" Verder was Koningsdag een zwart gat.")

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
    assert_equal(sf_set, {u"burgemeester", u"Amstelveen", u"M\xe1xima",
                          u"Koningsdag", u"zwart gat"})
    for ann in en_annotations:
        # The disambiguation candidates should be of type list
        assert_true(isinstance(ann['resource'], list))
        # There should be at least one candidate
        assert_greater(ann['resource'], 0)


def test_nlner_conll():
    text = "Oorspronkelijk kwam Pantchoulidzew uit het Russische Pjatigorsk"

    expected = [(u'Oorspronkelijk', 'O'), (u'kwam', 'O'),
                (u'Pantchoulidzew', 'B'), (u'uit', 'O'), (u'het', 'O'),
                (u'Russische', 'B'), (u'Pjatigorsk', 'I')]

    # nlner_conll is not entirely deterministic, so we have to strip off the
    # classes. (It tends to confuse PER and MISC.)
    # XXX Should we fix some random seed?
    tagged = nlner_conll(text)
    tagged = [(term, tag[0]) for term, tag in expected]
    assert_equal(tagged, expected)


def test_movie_review_emotions():
    text = "Saw is a scary film."

    sent, emo = zip(*movie_review_emotions(text))

    # We tend to get ('Fear', 'Joy', 'Love') or ('Fear', 'Love') for this
    # sentence.
    assert_equal(len(sent), 1)
    assert_equal(len(emo), 1)
    assert_in('Fear', emo[0])

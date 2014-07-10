"""
Test the CoreNLP parser/lemmatizer functions and task.
"""

import logging
from unittest import SkipTest
import os.path

from nose.tools import assert_equal, assert_not_equal, assert_in

from xtas.tasks._corenlp import parse, stanford_to_saf, get_corenlp_version
from xtas.tasks.single import corenlp, corenlp_lemmatize


def _check_corenlp():
    v = get_corenlp_version()
    if not v:
        raise SkipTest("CoreNLP not found at CORENLP_HOME")


def test_parse_xml():
    xml = open(os.path.join(os.path.dirname(__file__), "test_corenlp.xml")).read()
    saf = stanford_to_saf(xml)
    assert_equal({t['lemma'] for t in saf['tokens']},
                 {"John", "attack", "I", "in", "London", "hit", "he", "back", "."})
    london = [t for t in saf['tokens'] if t['lemma'] == 'London'][0]
    assert_equal(london['pos'], 'NNP')
    assert_in({"type": "LOCATION", "tokens": [london['id']]}, saf['entities'])


def test_lemmatize():
    _check_corenlp()
    lines = parse("He jumped. \n\n Cool!",
                  annotators=['tokenize', 'ssplit', 'pos', 'lemma'])
    saf = stanford_to_saf(lines)
    assert_equal(set(saf.keys()), {'tokens', 'header'})

    assert_equal({t['lemma'] for t in saf['tokens']},
                 {'he', 'jump', 'cool', '!', '.'})
    assert_equal({t['sentence'] for t in saf['tokens']},
                 {1, 2})


def test_lemmatize_unicode():
    _check_corenlp()
    lines = parse(u"\u0540\u0578\u057e\u056b\u056f hit C\xe9sar",
                  annotators=['tokenize', 'ssplit', 'pos', 'lemma'])
    saf = stanford_to_saf(lines)
    assert_equal({t['lemma'] for t in saf['tokens']},
                 {'Cesar', 'hit', 'Hovik'})


def test_ner():
    _check_corenlp()
    annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner']
    saf = stanford_to_saf(parse("John lives in Amsterdam",
                                annotators=annotators))
    lemmata = {t['id']: t['lemma'] for t in saf['tokens']}
    entities = {lemmata[e['tokens'][0]]: e['type'] for e in saf['entities']}
    assert_equal(entities, {'John': 'PERSON', 'Amsterdam': 'LOCATION'})


def test_parse():
    _check_corenlp()
    saf = stanford_to_saf(parse("John loves himself"))
    lemmata = {t['id']: t['lemma'] for t in saf['tokens']}
    assert_equal(saf['trees'], [{
        "tree": "(ROOT (S (NP (NNP John)) (VP (VBZ loves) "
                "(NP (PRP himself)))))",
        "sentence": 1
        }])
    deps = {(lemmata[d['child']], lemmata[d['parent']], d['relation'])
            for d in saf['dependencies']}
    assert_equal(deps, {('John', 'love', 'nsubj'),
                        ('himself', 'love', 'dobj')})
    corefs = {tuple(sorted([lemmata[c[0][0]], lemmata[c[1][0]]]))
              for c in saf['coreferences']}
    assert_equal(corefs, {tuple(sorted(['John', 'himself']))})


def test_task():
    _check_corenlp()
    raw = corenlp_lemmatize("It works", output='raw')
    assert_in("<lemma>work</lemma>", raw)  # list of header / sentence / tokens
    saf = corenlp_lemmatize("It works", output='saf')
    assert_equal(len(saf['tokens']), 2)

    raw = corenlp("It works", output='raw')
    assert_in('<dep type="nsubj">', raw)
    saf = corenlp("It works", output='saf')
    assert_equal(len(saf['dependencies']), 1)

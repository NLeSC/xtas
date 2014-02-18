"""
Test the CoreNLP parser/lemmatizer functions and task.
"""

import logging
from unittest import SkipTest

from nose.tools import assert_equal, assert_not_equal

from xtas.tasks._corenlp import parse, stanford_to_saf, get_corenlp_version
from xtas.tasks.single import corenlp, corenlp_lemmatize


def _check_corenlp():
    v = get_corenlp_version()
    if not v:
        raise SkipTest("CoreNLP not found at CORENLP_HOME")


def test_raw():
    _check_corenlp()
    lines = parse("It. Works\n", annotators=['tokenize', 'ssplit'])
    expected = ['Sentence #1 (2 tokens):', 'It.',
                '[Text=It CharacterOffsetBegin=0 CharacterOffsetEnd=2]'
                ' [Text=. CharacterOffsetBegin=2 CharacterOffsetEnd=3]',
                'Sentence #2 (1 tokens):', 'Works',
                '[Text=Works CharacterOffsetBegin=4 CharacterOffsetEnd=9]']
    assert_equal(lines, expected)


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
    assert_equal(len(raw), 3)  # list of header / sentence / tokens
    saf = corenlp_lemmatize("It works", output='saf')
    assert_equal(len(saf['tokens']), 2)

    raw = corenlp("It works", output='raw')
    deps = {'root(ROOT-0, works-2)', 'nsubj(works-2, It-1)', ''}
    assert_equal(set(raw[-3:]), deps)
    saf = corenlp("It works", output='saf')
    assert_equal(len(saf['dependencies']), 1)

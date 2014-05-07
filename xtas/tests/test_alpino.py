"""
Test the Alpino parser functions and task.
"""

import os
import os.path
import logging
from unittest import SkipTest

from nose.tools import assert_equal, assert_not_equal, assert_in

from xtas.tasks._alpino import (tokenize, parse_raw,
                                interpret_token, interpret_parse)
from xtas.tasks.single import alpino


_SENT = "Toob is dik"
_TOK_IS = "ben|is|1|2|verb|verb(copula)|verb(unacc,sg_heeft,copula)"
_TOK_TOOB = "Toob|Toob|0|1|name|name(PER)|proper_name(both,PER)"
_TOK_DIK = "dik|dik|2|3|adj|adj|adjective(no_e(adv))"
_PARSE = ("{ben}|hd/predc|{dik}|1\n{ben}|hd/su|{toob}|1"
          .format(ben=_TOK_IS, dik=_TOK_DIK, toob=_TOK_TOOB))


def _check_alpino():
    home = os.environ.get('ALPINO_HOME')
    if home is None:
        raise SkipTest("ALPINO_HOME not set, skipping alpino tests")
    if not os.path.exists(home):
        raise SkipTest("Alpino not found at ALPINO_HOME={}, skipping tests"
                       .format(home))


def test_tokenize():
    _check_alpino()
    text = u"D\xedt is een zin, met komma |nietwaar|? En nog 'n zin"
    expected = u"D\xedt is een zin , met komma nietwaar ?\nEn nog 'n zin\n"
    assert_equal(tokenize(text), expected.encode('utf-8'))


def test_parse():
    _check_alpino()
    deps = parse_raw(_SENT)
    assert_equal({dep for dep in deps.split("\n") if dep},
                 {dep for dep in _PARSE.split("\n") if dep})


def test_interpret_token():
    actual = interpret_token(*_TOK_TOOB.split("|"))
    expected = {'lemma': 'Toob', 'word': 'Toob', 'offset': 0,
                'pos': 'name', 'pos1': 'M',
                'pos_major': 'proper_name', 'pos_minor': 'both,PER'}
    assert_equal(actual, expected)


def test_interpret_parse():
    saf = interpret_parse(_PARSE)
    assert_equal({t['lemma'] for t in saf['tokens']}, {"Toob", "ben", "dik"})
    assert_equal(len(saf['dependencies']), 2)


def test_alpino_task():
    "Test whether the xtas.tasks.single.alpino call works"
    _check_alpino()
    assert_equal(alpino(_SENT, output='raw').strip(), _PARSE)
    saf = alpino(_SENT, output='saf')
    assert_equal(set(saf.keys()), {'header', 'tokens', 'dependencies'})


def test_alpino_unicode():
    "Test what happens with non-ascii characters in input"
    _check_alpino()
    text = u"Bjarnfre\xf0arson leeft"
    # tokenize should convery to utf-8 and only add final line break
    assert_equal(tokenize(text).decode("utf-8"), text + "\n")
    saf = alpino(text, output='saf')
    assert_equal({t['lemma'] for t in saf['tokens']},
                 {u"Bjarnfre\xf0arson", u"leef"})

    text = u"\u738b\u6bc5 ook"
    saf = alpino(text, output='saf')
    assert_equal({t['lemma'] for t in saf['tokens']},
                 {u"\u738b\u6bc5", u"ook"})

    text = u"E\xe9n test nog"
    saf = alpino(text, output='saf')
    assert_equal({t['lemma'] for t in saf['tokens']},
                 {u"\xe9\xe9n" ,"test", "nog"})

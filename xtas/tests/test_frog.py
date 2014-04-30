"""
Test the Frog lemmatizer functions and task.
"""

import logging
import socket
from unittest import SkipTest

from nose.tools import assert_equal, assert_not_equal

from xtas.tasks._frog import (FROG_HOST, FROG_PORT, call_frog, frog_to_saf,
                              parse_frog)


def _check_frog():
    s = socket.socket()
    try:
        s.connect((FROG_HOST, FROG_PORT))
    except:
        logging.exception("Unable to connect to {}:{}, skipping tests"
                          .format(FROG_HOST, FROG_PORT))
        raise SkipTest("Cannot connect to frog, skipping tests")

    logging.info("Frog is alive!")


def test_call_frog():
    _check_frog()
    lines = list(call_frog("dit is in Amsterdam. Tweede zin!"))
    assert_equal(len(lines), 10)
    test = lines[3].split("\t")[:5]
    assert_equal(test, ['4', 'Amsterdam', 'Amsterdam', '[Amsterdam]',
                        'SPEC(deeleigen)'])
    assert_equal(lines[5], '')


LINES = ['1\tdit\tdit\t[dit]\tVNW(aanw,pron,stan,vol,3o,ev)\t0.9\tO\tB-NP\t\t',
         '2\tis\tzijn\t[zijn]\tWW(pv,tgw,ev)\t0.9\tO\tB-VP\t\t',
         '3\tin\tin\t[in]\tVZ(init)\t0.998321\tO\tB-PP\t\t',
         '4\tAmsterdam\tAmsterdam\t[Amsterdam]\tSPEC(deeleigen)'
         '\t1.000000\tB-LOC\tB-NP\t\t',
         '5\t.\t.\t[.]\tLET()\t0.999956\tO\tO\t\t',
         '',
         '1\tTweede\ttwee\t[twee][de]\tTW(rang,prenom,stan)\t0.9\tO\tB-NP\t\t',
         '2\tzin\tzin\t[zin]\tN(soort,ev,basis,zijd,stan)\t0.99\tO\tI-NP\t\t',
         '3\t!\t!\t[!]\tLET()\t0.995005\tO\tO\t\t',
         '']


def test_parse_frog():
    tokens = list(parse_frog(LINES))
    assert_equal(len(tokens), 8)
    expected = dict(id=0, sentence=0,
                    lemma='dit', word='dit',
                    pos='VNW(aanw,pron,stan,vol,3o,ev)',
                    pos_confidence=0.9)
    assert_equal(tokens[0], expected)
    assert_equal(tokens[7]['sentence'], 1)


def test_frog_to_saf():
    tokens = list(parse_frog(LINES))
    saf = frog_to_saf(tokens)
    assert_equal(len(saf['tokens']), 8)
    token = [t for t in saf['tokens'] if t['lemma'] == 'Amsterdam']
    assert_equal(len(token), 1)
    assert_equal(token[0]['pos1'], 'M')


def test_frog_task():
    "Test whether the xtas.tasks.single.frog call works"
    _check_frog()
    from xtas.tasks.single import frog
    raw = frog("dit is een test", output='raw')
    assert_equal(len(raw), 5)
    assert_equal(raw[4], '')
    tokens = frog("dit is een test", output='tokens')
    assert_equal(len(tokens), 4)
    assert_equal(tokens[0]['lemma'], 'dit')
    saf = frog("dit is een test", output='saf')
    assert_equal(len(saf['tokens']), 4)
    assert_equal(saf['header']['processed'][0]['module'], 'frog')

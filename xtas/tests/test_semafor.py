"""
Test the Semafor semantic parser
All tests require semafor to be listening to SEMAFOR_HOST:SEMAFOR_PORT
(default localhost:9888).
The to_conll and add_frames also require CORENLP_HOME to point to a
CoreNLP installation dir.
"""

import os
import socket
from unittest import SkipTest

from nose.tools import assert_equal, assert_not_equal


def _check_corenlp_home():
    if not os.environ.get("CORENLP_HOME"):
        raise SkipTest("Cannot find CORENLP_HOME")


def _check_semafor():
    host = os.environ.get("SEMAFOR_HOST", "localhost")
    port = int(os.environ.get("SEMAFOR_PORT", 9888))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = s.connect_ex((host, port))
        if(result != 0):
            raise SkipTest("Semafor web service not listening to {host}:{port}"
                           .format(**locals()))
    finally:
        s.close()


def test_to_conll():
    "Test conversion of Penn Trees to conll using corenlp"
    from xtas.tasks._semafor import to_conll
    _check_corenlp_home()

    result = to_conll(TEST_TREE)

    deps = [x for x in result.split("\n") if x.strip()]

    assert_equal(deps, TEST_CONLL)


def test_semafor():
    "Test raw semafor output"
    from xtas.tasks._semafor import call_semafor
    _check_semafor()

    conll = "\n".join(TEST_CONLL)
    frames = call_semafor(conll)
    # 1 frame in 1 sentence
    assert_equal(len(frames), 1)
    assert_equal(len(frames[0]['frames']), 1)
    # about love!
    f = frames[0]['frames'][0]
    assert_equal(f['target']['name'], 'Experiencer_focus')
    assert_equal(f['target']['spans'][0]['text'], 'loves')


def test_add_frames():
    from xtas.tasks._semafor import add_frames
    _check_semafor()
    _check_corenlp_home()

    saf = add_frames(TEST_SAF)

    tokens = {t['id']: t['word'] for t in saf['tokens']}
    assert_equal(len(saf['frames']), 1)
    assert_equal(saf['frames'][0]['name'], 'Experiencer_focus')
    assert_equal({tokens[t] for t in saf['frames'][0]['target']}, {'loves'})


def test_task():
    "Test the celery task"
    from xtas.tasks.single import semafor
    _check_semafor()
    _check_corenlp_home()

    saf = semafor(TEST_SAF)
    assert_equal(len(saf['frames']), 1)


TEST_TREE = "(ROOT (S (NP (NNP John)) (VP (VBZ loves) (NP (NNP Mary)))))"

TEST_CONLL = ['1\tJohn\t_\tNNP\tNNP\t_\t2\tnsubj\t_\t_',
              '2\tloves\t_\tVBZ\tVBZ\t_\t0\troot\t_\t_',
              '3\tMary\t_\tNNP\tNNP\t_\t2\tdobj\t_\t_']

TEST_SAF = {
    "header": {
        "format-version": "0.0",
        "processed": [
            {
                "module-version": "3.3.1",
                "module": "corenlp"
            }
        ],
        "format": "SAF"
    },
    "tokens": [
        {
            "word": "John",
            "sentence": 1,
            "offset": "0",
            "id": 1
        },
        {
            "word": "loves",
            "sentence": 1,
            "offset": "5",
            "id": 2
        },
        {
            "word": "Mary",
            "sentence": 1,
            "offset": "11",
            "id": 3
        }
    ],
    "trees": [
        {
            "tree": TEST_TREE,
            "sentence": 1
        }
    ]
}

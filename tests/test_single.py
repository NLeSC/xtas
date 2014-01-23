from nose.tools import assert_equal

from xtas.tasks import tokenize


class MockDocument(object):
    def __init__(self, text):
        self.text = text

    def fetch(self):
        return self.text


def test_tokenize():
    doc = MockDocument("My hovercraft is full of eels.")
    tokens = tokenize(doc)
    expected = "My hovercraft is full of eels .".split()
    for obs, exp in zip(tokens, expected):
        assert_equal(obs, {"token": exp})

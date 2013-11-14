from nose.tools import assert_equal

import langid
from xtas.tasks import run_langid


def test_langid():
    """Assert that run_langid's output is just that from langid.

    ... and that langid does something sensible
    """

    # don't run a source code spellchecker on this file.
    text = """Parallal tesk distributoin is trickey."""

    our_results = run_langid(text, {})
    ground_truth = langid.rank(text)

    assert_equal(ground_truth, our_results)

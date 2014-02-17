"""
Test the pipelining and caching in xtas
"""

from nose.tools import assert_equal, assert_not_equal

from contextlib import contextmanager

@contextmanager
def eager_celery():
    from xtas.tasks import app
    old_value = app.conf['CELERY_ALWAYS_EAGER']
    app.conf['CELERY_ALWAYS_EAGER'] = True
    try:
        yield
    finally:
        app.conf['CELERY_ALWAYS_EAGER'] = old_value
        

def test_pipeline():
    from xtas.tasks import tokenize, pos_tag, get_results
    s = "cats are furry"
    expected = [('cats', 'NNS'), ('are', 'VBP'), ('furry', 'JJ')]
    result = pos_tag(tokenize(s), 'nltk')
    assert_equal(result, expected)
    with eager_celery():
        # do we get correct result from pipeline?
        r = get_results(s, [{"module" : tokenize}, {"module": pos_tag, "arguments" : {"model" : "nltk"}}])
        assert_equal(r, expected)
        # can we specify modules by name?
        r = get_results(s, [{"module" : "xtas.tasks.tokenize"}, {"module": "xtas.tasks.pos_tag", "arguments" : {"model" : "nltk"}}])
        assert_equal(r, expected)

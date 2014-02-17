"""
Test the pipelining and caching in xtas
"""

from contextlib import contextmanager

from nose.tools import assert_equal, assert_not_equal

from xtas.utils import clean_es
ES_TEST_TYPE = "unittest_doc"

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
    from xtas.tasks import tokenize, pos_tag, pipeline
    s = "cats are furry"
    expected = [('cats', 'NNS'), ('are', 'VBP'), ('furry', 'JJ')]
    result = pos_tag(tokenize(s), 'nltk')
    assert_equal(result, expected)
    with eager_celery():
        # do we get correct result from pipeline?
        r = pipeline(s, [{"module" : tokenize}, {"module": pos_tag, "arguments" : {"model" : "nltk"}}])
        assert_equal(r, expected)
        # can we specify modules by name?
        r = pipeline(s, [{"module" : "xtas.tasks.tokenize"}, {"module": "xtas.tasks.pos_tag", "arguments" : {"model" : "nltk"}}])
        assert_equal(r, expected)


def test_pipeline_cache():
    "Does the cache work correctly?"
    import json
    import nltk
    from xtas.tasks import tokenize, pos_tag, pipeline, es_document
    text = "The cat is happy"
    expected_tokens= [{u'token': u'The'}, {u'token': u'cat'}, {u'token': u'is'}, {u'token': u'happy'}]
    expected_pos = [[u'The', u'DT'], [u'cat', u'NN'], [u'is', u'VBZ'], [u'happy', u'JJ']]
    with eager_celery(), clean_es() as (idx, es):
        id = es.index(index=idx, doc_type=ES_TEST_TYPE, body={"text" : text})['_id']
        doc = es_document(idx, ES_TEST_TYPE, id, "text")
        # test a single task 'pipeline'
        pipe = [{"module" : tokenize}]
        r = pipeline(doc, pipe, store_intermediate=True)
        assert_equal(r, expected_tokens)
        # second time result should come from cache. Test with block=False (returns async object if not cached)
        r = pipeline(doc, pipe, store_intermediate=True, block=False)
        assert_equal(r, expected_tokens)
        # add pos_tag to pipeline. Check that tokenize is not called (more elegant way to check that?)
        pipe = [{"module" : "xtas.tasks.tokenize"}, {"module": "xtas.tasks.pos_tag", "arguments" : {"model" : "nltk"}}]
        OLD_TOKENIZE = nltk.word_tokenize
        nltk.word_tokenize = None
        try:
            r = pipeline(doc, pipe, store_intermediate=True)
            assert_equal(json.dumps(r), json.dumps(expected_pos)) # compare json to ignore tuple/list difference
        finally:
            nltk.word_tokenize = OLD_TOKENIZE
        # whole pipeline should now be skipped
        r = pipeline(doc, pipe, store_intermediate=True, block=False)
        assert_equal(json.dumps(r), json.dumps(expected_pos)) 


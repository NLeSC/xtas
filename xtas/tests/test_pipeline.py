"""
Test the pipelining and caching in xtas
"""

from contextlib import contextmanager

from nose.tools import assert_equal

from xtas.tests.test_es import clean_es, ES_TEST_INDEX

from elasticsearch import client

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
    from xtas.tasks.single import tokenize, pos_tag
    from xtas.tasks.pipeline import pipeline
    s = "cats are furry"
    expected = [('cats', 'NNS'), ('are', 'VBP'), ('furry', 'JJ')]
    result = pos_tag(tokenize(s), 'nltk')
    assert_equal(result, expected)
    with eager_celery():
        # do we get correct result from pipeline?
        r = pipeline(s, [{"task": tokenize},
                         {"task": pos_tag, "arguments": {"model": "nltk"}}])
        assert_equal(r, expected)
        # is the old syntax still supported?
        r = pipeline(s, [{"module": tokenize},
                         {"module": pos_tag, "arguments": {"model": "nltk"}}])
        assert_equal(r, expected)
        # can we specify modules by name?
        r = pipeline(s, [{"task": "xtas.tasks.single.tokenize"},
                         {"task": "xtas.tasks.single.pos_tag",
                          "arguments": {"model": "nltk"}}])
        assert_equal(r, expected)


def test_pipeline_cache():
    "Does the cache work correctly?"
    import json
    import nltk
    from xtas.tasks.single import tokenize
    from xtas.tasks.pipeline import pipeline
    from xtas.tasks.es import es_document
    text = "The cat is happy"
    expected_tokens = [u'The', u'cat', u'is', u'happy']
    expected_pos = [[u'The', u'DT'], [u'cat', u'NN'],
                    [u'is', u'VBZ'], [u'happy', u'JJ']]
    with eager_celery(), clean_es() as es:
        idx, typ = ES_TEST_INDEX, ES_TEST_TYPE
        id = es.index(index=idx, doc_type=typ, body={"text": text})['_id']
        doc = es_document(idx, typ, id, "text")
        # test a single task 'pipeline'
        pipe = [{"module": tokenize}]
        r = pipeline(doc, pipe, store_intermediate=True)
        assert_equal(r, expected_tokens)
        # second time result should come from cache.
        # Test with block=False which returns async object if not cached
        client.indices.IndicesClient(es).flush()
        r = pipeline(doc, pipe, store_intermediate=True, block=False)
        assert_equal(r, expected_tokens)
        # add pos_tag to pipeline. Check that tokenize is not called
        # (anyone has a more elegant way to check that?)
        pipe = [{"module": "xtas.tasks.single.tokenize"},
                {"module": "xtas.tasks.single.pos_tag",
                 "arguments": {"model": "nltk"}}]
        OLD_TOKENIZE = nltk.word_tokenize
        nltk.word_tokenize = None
        try:
            client.indices.IndicesClient(es).flush()
            r = pipeline(doc, pipe, store_intermediate=True)
            # compare json to ignore tuple/list difference
            assert_equal(json.dumps(r), json.dumps(expected_pos))
        finally:
            nltk.word_tokenize = OLD_TOKENIZE
        # whole pipeline should now be skipped
        client.indices.IndicesClient(es).flush()
        r = pipeline(doc, pipe, store_intermediate=True, block=False)
        assert_equal(json.dumps(r), json.dumps(expected_pos))

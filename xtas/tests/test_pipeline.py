"""
Test the pipelining and caching in xtas
"""

from contextlib import contextmanager

from nose.tools import assert_equal

from test_es import clean_es, ES_TEST_INDEX

ES_TEST_TYPE = "unittest_doc"
import json

@contextmanager
def eager_celery():
    from xtas.tasks import app
    old_value = app.conf['CELERY_ALWAYS_EAGER']
    app.conf['CELERY_ALWAYS_EAGER'] = True
    try:
        yield
    finally:
        app.conf['CELERY_ALWAYS_EAGER'] = old_value

def _makedoc(es, text, id=None):
    from xtas.tasks.es import es_document
    idx, typ = ES_TEST_INDEX, ES_TEST_TYPE
    id = es.index(index=idx, doc_type=typ, body={"text": text}, id=id)['_id']
    return es_document(idx, typ, id, "text")

def test_pipeline_cache_multiple():
    from xtas.tasks.single import tokenize, pos_tag
    from xtas.tasks.pipeline import pipeline_multiple, pipeline
    pipe = [{"module": tokenize},
            {"module": pos_tag, "arguments": {"model": "nltk"}}]

    texts =["cats are furry", "cats are cute", "some cats are fat"]
    expected = [[['cats', 'NNS'], ['are', 'VBP'], ['furry', 'JJ']],
                [['cats', 'NNS'], ['are', 'VBP'], ['cute', 'JJ']],
                [['my', 'PRP$'], ['cat', 'NN'], ['is', 'VBZ'], ['stupid', 'JJ']],
                [['some', 'DT'], ['cats', 'NNS'], ['are', 'VBP'], ['fat', 'JJ']]]

    with eager_celery(), clean_es() as es:
        docs = [_makedoc(es, text, i) for i, text in enumerate(texts)]
        docs.append("my cat is stupid")

        # add some docs to cache: fully cache first doc, partially cache second
        pipeline(docs[0], pipe)
        pipeline(docs[1], pipe[:1])

        results = pipeline_multiple(docs, pipe, store_intermediate=True)

        results = json.loads(json.dumps(results))
        expected = json.loads(json.dumps(expected))

        assert_equal(sorted(results), sorted(expected))


def test_pipeline():
    from xtas.tasks.single import tokenize, pos_tag
    from xtas.tasks.pipeline import pipeline
    s = "cats are furry"
    expected = [('cats', 'NNS'), ('are', 'VBP'), ('furry', 'JJ')]
    result = pos_tag(tokenize(s), 'nltk')
    assert_equal(result, expected)
    with eager_celery():
        # do we get correct result from pipeline?
        r = pipeline(s, [{"module": tokenize},
                         {"module": pos_tag, "arguments": {"model": "nltk"}}])
        assert_equal(r, expected)
        # can we specify modules by name?
        r = pipeline(s, [{"module": "xtas.tasks.single.tokenize"},
                         {"module": "xtas.tasks.single.pos_tag",
                          "arguments": {"model": "nltk"}}])
        assert_equal(r, expected)


def test_pipeline_cache():
    "Does the cache work correctly?"
    import json
    import nltk
    from xtas.tasks.single import tokenize
    from xtas.tasks.pipeline import pipeline
    text = "The cat is happy"
    expected_tokens = [{u'token': u'The'}, {u'token': u'cat'},
                       {u'token': u'is'}, {u'token': u'happy'}]
    expected_pos = [[u'The', u'DT'], [u'cat', u'NN'],
                    [u'is', u'VBZ'], [u'happy', u'JJ']]
    with eager_celery(), clean_es() as es:
        doc = _makedoc(es, text)

        # test a single task 'pipeline'
        pipe = [{"module": tokenize}]
        r = pipeline(doc, pipe, store_intermediate=True)
        assert_equal(r, expected_tokens)
        # add pos_tag to pipeline. Check that tokenize is not called
        # (anyone has a more elegant way to check that?)
        pipe = [{"module": "xtas.tasks.single.tokenize"},
                {"module": "xtas.tasks.single.pos_tag",
                 "arguments": {"model": "nltk"}}]
        OLD_TOKENIZE = nltk.word_tokenize
        nltk.word_tokenize = None
        try:
            r = pipeline(doc, pipe, store_intermediate=True)
            # compare json to ignore tuple/list difference
            assert_equal(json.dumps(r), json.dumps(expected_pos))
        finally:
            nltk.word_tokenize = OLD_TOKENIZE

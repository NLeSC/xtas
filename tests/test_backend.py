from nose.tools import assert_equal, assert_not_equal
from unittest import SkipTest
import logging
from contextlib import contextmanager

from elasticsearch import Elasticsearch, client

ES_TEST_INDEX = "xtas__unittest"
ES_TEST_TYPE = "unittest_doc"

@contextmanager
def clean_es():
    "provide a clean elasticsearch instance for unittests"
    es = Elasticsearch()
    if not ES_TEST_INDEX:
        raise SkipTest("ES_TEST_INDEX not given, skipping elastic tests")
    es = Elasticsearch()
    indexclient = client.indices.IndicesClient(es)
    if not es.ping():
        raise SkipTest("ElasticSearch host not found, skipping elastic tests")
    logging.info("deleting and recreating index {ES_TEST_INDEX} at {ES_TEST_HOST}")
    if indexclient.exists(ES_TEST_INDEX):
        indexclient.delete(ES_TEST_INDEX)
    indexclient.create(ES_TEST_INDEX)
    try:
        yield es
    finally:
        indexclient.delete(ES_TEST_INDEX)
            

def test_fetch():
    "Test whether tasks.fetch works as documented"
    from xtas.tasks import fetch, es_document
    # if doc is a string, fetching should return the string
    assert_equal(fetch("Literal string"), "Literal string")
    # index a document and fetch it with an es_document
    with clean_es() as es:
        d = es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test"})
        doc = es_document(ES_TEST_INDEX, ES_TEST_TYPE, d['_id'], "text")
        assert_equal(fetch(doc), "test")

def test_query_batch():
    "Test getting multiple documents in a batch"
    from xtas.tasks import fetch_query_batch
    with clean_es() as es:
        d1 = es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test", "test":"batch"})
        d2 = es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test2", "test":"batch"})
        d3 = es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"test":"batch"})
        client.indices.IndicesClient(es).flush()
        b = fetch_query_batch(ES_TEST_INDEX, ES_TEST_TYPE, query={"term" : {"test" : "batch"}}, field="text")
        assert_equal(set(b), {"test", "test2"})

def test_store_single():
    "Test storing results as a 'xtas_results' object on the document"
    from xtas.tasks import store_single
    with clean_es() as es:
        id = es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test"})['_id']
        # store a task result, check if it is properly stored
        store_single("task1_result", "task1", ES_TEST_INDEX, ES_TEST_TYPE, id)
        src = es.get_source(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, id=id)
        assert_equal(set(src['xtas_results'].keys()), {'task1'})
        assert_equal(src['xtas_results']['task1']['data'], 'task1_result')
        # store a second task result, check if both are now stored
        store_single("task2_result", "task2", ES_TEST_INDEX, ES_TEST_TYPE, id)
        src = es.get_source(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, id=id)
        assert_equal(set(src['xtas_results'].keys()), {'task1', 'task2'})
        assert_equal(src['xtas_results']['task2']['data'], 'task2_result')
        # store a task result under an existing task, check that it is replaced
        store_single("task1_new_result", "task1", ES_TEST_INDEX, ES_TEST_TYPE, id)
        src = es.get_source(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, id=id)
        assert_equal(set(src['xtas_results'].keys()), {'task1', 'task2'})
        assert_equal(src['xtas_results']['task1']['data'], 'task1_new_result')

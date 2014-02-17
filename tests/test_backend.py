from nose.tools import assert_equal, assert_not_equal
from unittest import SkipTest
import logging
from contextlib import contextmanager

from elasticsearch import Elasticsearch, client
from xtas.utils import clean_es

ES_TEST_TYPE = "unittest_doc"


def test_fetch():
    "Test whether tasks.fetch works as documented"
    from xtas.tasks import fetch, es_document
    # if doc is a string, fetching should return the string
    assert_equal(fetch("Literal string"), "Literal string")
    # index a document and fetch it with an es_document
    with clean_es() as (idx, es):
        d = es.index(index=idx, doc_type=ES_TEST_TYPE, body={"text" : "test"})
        doc = es_document(idx, ES_TEST_TYPE, d['_id'], "text")
        assert_equal(fetch(doc), "test")


def test_query_batch():
    "Test getting multiple documents in a batch"
    from xtas.tasks import fetch_query_batch
    with clean_es() as (idx, es):
        d1 = es.index(index=idx, doc_type=ES_TEST_TYPE, body={"text" : "test", "test":"batch"})
        d2 = es.index(index=idx, doc_type=ES_TEST_TYPE, body={"text" : "test2", "test":"batch"})
        d3 = es.index(index=idx, doc_type=ES_TEST_TYPE, body={"test":"batch"})
        client.indices.IndicesClient(es).flush()
        b = fetch_query_batch(idx, ES_TEST_TYPE, query={"term" : {"test" : "batch"}}, field="text")
        assert_equal(set(b), {"test", "test2"})


def test_store_single():
    "Test storing results as a 'xtas_results' object on the document"
    from xtas.tasks import store_single
    with clean_es() as (idx, es):
        id = es.index(index=idx, doc_type=ES_TEST_TYPE, body={"text" : "test"})['_id']
        # store a task result, check if it is properly stored
        store_single("task1_result", "task1", idx, ES_TEST_TYPE, id)
        src = es.get_source(index=idx, doc_type=ES_TEST_TYPE, id=id)
        assert_equal(set(src['xtas_results'].keys()), {'task1'})
        assert_equal(src['xtas_results']['task1']['data'], 'task1_result')

        # store a second task result, check if both are now stored
        store_single("task2_result", "task2", idx, ES_TEST_TYPE, id)
        src = es.get_source(index=idx, doc_type=ES_TEST_TYPE, id=id)
        assert_equal(set(src['xtas_results'].keys()), {'task1', 'task2'})
        assert_equal(src['xtas_results']['task2']['data'], 'task2_result')

        # store a task result under an existing task, check that it is replaced
        store_single("task1_new_result", "task1", idx, ES_TEST_TYPE, id)
        src = es.get_source(index=idx, doc_type=ES_TEST_TYPE, id=id)
        assert_equal(set(src['xtas_results'].keys()), {'task1', 'task2'})
        assert_equal(src['xtas_results']['task1']['data'], 'task1_new_result')

        # check that the rest of the document is intact
        assert_equal(set(src.keys()), {'text', 'xtas_results'})
        assert_equal(src['text'], "test")


def test_get_result():
    from xtas.tasks import store_single, get_single_result
    with clean_es() as (idx, es):
        id = es.index(index=idx, doc_type=ES_TEST_TYPE, body={"text" : "test"})['_id']
        assert_equal(get_single_result("task1", idx, ES_TEST_TYPE, id), None)
        store_single("task1_result", "task1", idx, ES_TEST_TYPE, id)
        assert_equal(get_single_result("task1", idx, ES_TEST_TYPE, id), "task1_result")

import unittest, os
import logging
from elasticsearch import Elasticsearch, client

ES_TEST_INDEX = "xtas__unittest"
ES_TEST_HOSTS = [{"host": "localhost", "port": 9200}]
ES_TEST_TYPE = "unittest_doc"

class TestBackend(unittest.TestCase):

    def setUp(self):
        if not ES_TEST_INDEX:
            raise unittest.SkipTest("ES_TEST_INDEX not given, skipping elastic tests")
        self.es = Elasticsearch(hosts=ES_TEST_HOSTS)
        self.indexclient = client.indices.IndicesClient(self.es)
        if not self.es.ping():
            raise unittest.SkipTest("ElasticSearch host not found, skipping elastic tests")
        logging.info("deleting and recreating index {ES_TEST_INDEX} at {ES_TEST_HOST}")
        if self.indexclient.exists(ES_TEST_INDEX):
            self.indexclient.delete(ES_TEST_INDEX)
        self.indexclient.create(ES_TEST_INDEX)

    def test_fetch(self):
        "Test whether tasks.fetch works as documented"
        from xtas.tasks import fetch, es_document
        # if doc is a string, fetching should return the string
        self.assertEqual(fetch("Literal string"), "Literal string")
        # index a document and fetch it with an es_document
        d = self.es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test"})
        doc = es_document(ES_TEST_INDEX, ES_TEST_TYPE, d['_id'], "text")
        self.assertEqual(fetch(doc), "test")

    def test_query_batch(self):
        "Test getting multiple documents in a batch"
        from xtas.tasks import fetch_query_batch
        d1 = self.es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test", "test":"batch"})
        d2 = self.es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test2", "test":"batch"})
        d3 = self.es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"test":"batch"})
        self.indexclient.flush()
        b = fetch_query_batch(ES_TEST_INDEX, ES_TEST_TYPE, query={"term" : {"test" : "batch"}}, field="text")
        self.assertEqual(set(b), {"test", "test2"})

    def test_store_single(self):
        "Test storing results as a 'xtas_results' object on the document"
        from xtas.tasks import store_single
        id = self.es.index(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, body={"text" : "test"})['_id']
        self.indexclient.flush()
        store_single("task1_result", "task1", ES_TEST_INDEX, ES_TEST_TYPE, id)
        src = self.es.get_source(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, id=id)
        self.assertEqual(set(src['xtas_results'].keys()), {'task1'})
        self.assertEqual(src['xtas_results']['task1']['data'], 'task1_result')
        store_single("task2_result", "task2", ES_TEST_INDEX, ES_TEST_TYPE, id)
        src = self.es.get_source(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, id=id)
        self.assertEqual(set(src['xtas_results'].keys()), {'task1', 'task2'})
        self.assertEqual(src['xtas_results']['task2']['data'], 'task2_result')
        store_single("task1_new_result", "task1", ES_TEST_INDEX, ES_TEST_TYPE, id)
        src = self.es.get_source(index=ES_TEST_INDEX, doc_type=ES_TEST_TYPE, id=id)
        self.assertEqual(set(src['xtas_results'].keys()), {'task1', 'task2'})
        self.assertEqual(src['xtas_results']['task1']['data'], 'task1_new_result')
        
    def tearDown(self):
        if hasattr(self, 'indexclient') and self.indexclient.exists(ES_TEST_INDEX):
            self.indexclient.delete(ES_TEST_INDEX)
            

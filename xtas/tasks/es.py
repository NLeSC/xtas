"""Elasticsearch stuff."""

from __future__ import absolute_import

from datetime import datetime

from elasticsearch import Elasticsearch

from ..celery import app

_es = Elasticsearch()


_ES_DOC_FIELDS = ('index', 'type', 'id', 'field')


def es_document(idx, typ, id, field):
    """Returns a handle on a document living in the ES store.

    Returns a dict instead of a custom object to ensure JSON serialization
    works.
    """
    return {'index': idx, 'type': typ, 'id': id, 'field': field}


def fetch(doc):
    """Fetch document (if necessary).

    Parameters
    ----------
    doc : {dict, string}
        A dictionary representing a handle returned by es_document, or a plain
        string.
    """
    if isinstance(doc, dict) and set(doc.keys()) == set(_ES_DOC_FIELDS):
        idx, typ, id, field = [doc[k] for k in _ES_DOC_FIELDS]
        return _es.get_source(index=idx, doc_type=typ, id=id)[field]
    else:
        # Assume simple string
        return doc


@app.task
def fetch_query_batch(idx, typ, query, field='body'):
    """Fetch all documents matching query and return them as a list.

    Returns a list of field contents, with documents that don't have the
    required field silently filtered out.
    """
    r = _es.search(index=idx, doc_type=typ, body={'query': query},
                   fields=[field])
    r = (hit.get('fields', {}).get(field, None) for hit in r['hits']['hits'])
    return [hit for hit in r if hit is not None]


@app.task
def store_single(data, taskname, idx, typ, id):
    """Store the data in the xtas_results.taskname property of the document."""
    now = datetime.now().isoformat()
    doc = {"xtas_results": {taskname: {'data': data, 'timestamp': now}}}
    _es.update(index=idx, doc_type=typ, id=id, body={"doc": doc})
    return data

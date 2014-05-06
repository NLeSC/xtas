"""Elasticsearch stuff."""

from __future__ import absolute_import

from datetime import datetime

from chardet import detect as chardetect
from elasticsearch import Elasticsearch

from ..core import app, _config


def _es():
    return Elasticsearch(hosts=_config['ELASTICSEARCH'])


_ES_DOC_FIELDS = ('index', 'type', 'id', 'field')


def es_document(idx, typ, id, field):
    """Returns a handle on a field in a document living in the ES store.

    This does not fetch the document, or even check that it exists.
    """
    # Returns a dict instead of a custom object to ensure JSON serialization
    # works.
    return {'index': idx, 'type': typ, 'id': id, 'field': field}


def fetch(doc):
    """Fetch document (if necessary).

    Parameters
    ----------
    doc : {dict, string}
        A dictionary representing a handle returned by es_document, or a plain
        string. A Unicode string (Python 2 unicode, Python 3 str) will be
        returned as-is. A byte string (Python 2 str, Python 3 bytes) will be
        run through chardet to guess the encoding, then decoded with
        errors="replace".

    Returns
    -------
    content : string
        Document contents.
    """
    if isinstance(doc, dict) and set(doc.keys()) == set(_ES_DOC_FIELDS):
        idx, typ, id, field = [doc[k] for k in _ES_DOC_FIELDS]
        return _es().get_source(index=idx, doc_type=typ, id=id)[field]
    elif isinstance(doc, unicode):
        return doc
    elif isinstance(doc, str):
        enc = chardetect(doc)['encoding']
        return doc.decode(enc, errors="replace")
    else:
        raise TypeError("fetch expected es_document or string, got %s"
                        % type(doc))


@app.task
def fetch_query_batch(idx, typ, query, field='body'):
    """Fetch all documents matching query and return them as a list.

    Returns a list of field contents, with documents that don't have the
    required field silently filtered out.
    """
    r = _es().search(index=idx, doc_type=typ, body={'query': query},
                   _source=[field])
    r = (hit['_source'].get(field, None) for hit in r['hits']['hits'])
    return [hit for hit in r if hit is not None]


@app.task
def store_single(data, taskname, idx, typ, id, return_data=True):
    """Store the data in the xtas_results.taskname property of the document.

    If return_data is true, also returns data (useful for debugging). Set this
    to false to save bandwidth.
    """
    now = datetime.now().isoformat()
    doc = {"xtas_results": {taskname: {'data': data, 'timestamp': now}}}
    _es().update(index=idx, doc_type=typ, id=id, body={"doc": doc})
    return data if return_data else None


def get_all_results(idx, typ, id):
    """
    Get all xtas results for the document
    Returns a (possibly empty) {taskname : data} dict
    """
    r = _es().get(index=idx, doc_type=typ, id=id, _source=['xtas_results'])
    if 'xtas_results' in r['_source']:
        return {k: v['data']
                for (k, v) in r['_source']['xtas_results'].iteritems()}
    else:
        return {}


def get_single_result(taskname, idx, typ, id):
    """Get a single xtas result"""
    r = get_all_results(idx, typ, id)
    return r.get(taskname)

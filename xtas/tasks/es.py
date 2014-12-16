"""Elasticsearch stuff."""

from __future__ import absolute_import
from datetime import datetime

from elasticsearch import Elasticsearch, client, exceptions
from six import iteritems

from chardet import detect as chardetect

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
def fetch_query_batch(idx, typ, query, field='body', full=True):
    """Fetch all documents matching query and return them as a list.

    Returns a list of field contents, with documents that don't have the
    required field silently filtered out.
    """
    r = _es().search(index=idx, doc_type=typ, body={'query': query},
                   _source=[field])
    print r
    r = ((hit['_id'], hit['_source'].get(field, None)) for hit in r['hits']['hits'])
    if full:
      # This is disgusting and slow. Must find a way to put it into a query
      tasks = get_tasks_per_index(idx, typ)
    return [hit[1] for hit in r if hit is not None]

CHECKED_MAPPINGS = set()


def _check_parent_mapping(idx, child_type, parent_type):
    """
    Check that a mapping for the child_type exists
    Creates a new mapping with parent_type if needed
    This will fail horrifically if index1 is created and then deleted, because it will keep the index, child_type in memory.
    """
    if  not (idx, child_type) in CHECKED_MAPPINGS:
        indices_client = client.indices.IndicesClient(_es())
        if not indices_client.exists_type(idx, child_type):
            body = {child_type: {"_parent": {"type": parent_type}}}
            indices_client.put_mapping(index=idx, doc_type=child_type,
                                       body=body)
        CHECKED_MAPPINGS.add((idx, child_type))

@app.task
def store_single(data, taskname, idx, typ, id):
    """Store the data as a child document."""
    child_type = _taskname_to_child_type(taskname, typ) 
    _check_parent_mapping(idx, child_type, typ)
    #CHECKED_MAPPINGS = set({})
    now = datetime.now().isoformat()
    doc = {'data': data, 'timestamp': now}
    _es().index(index=idx, doc_type=child_type, id=id, body=doc, parent=id)
    return data

def _child_type_to_taskname(child_type):
  """Gets the taskname from the child_type of an xtas result"""
  try:
    typ, taskname = child_type.split("__", 1)
  except ValueError:
    return None
  return taskname

def _taskname_to_child_type(taskname, typ):
  """Transforms the taskname into a child_type"""
  return "{typ}__{taskname}".format(**locals())

def get_tasks_per_index(idx, typ):
  """Lists the tasks that were performed on the given index
     for documents of a specific type.
     Uses call on elastic search instead of the internal CHECKED_MAPPINGS to actually check the index.
  """
  try:
    indices_client = client.indices.IndicesClient(_es())
    r = indices_client.get_mapping(index=idx)[idx]
    tasks = set([])
    if not 'mappings' in r: return tasks
    for mapping_type, mapping in r['mappings'].iteritems():
      if '_parent' in mapping:
        if mapping['_parent']['type'] == typ:
          tasks.add(_child_type_to_taskname(mapping_type))
    return tasks
  except exceptions.TransportError, e:
      if e.status_code != 404:
         raise

def get_all_results(idx, typ, id):
  """
    Get all xtas results that exist for a document
    Returns a (possibly empty) {taskname : data} dict
  """
  results = {}
  for taskname in get_tasks_per_index(idx, typ):
    results[taskname] = get_single_result(taskname, idx, typ, id)
  return results

def get_single_result(taskname, idx, typ, id):
    """Get a single xtas result"""
    child_type = _taskname_to_child_type(taskname, typ)
    try:
        r = _es().get_source(index=idx, doc_type=child_type, id=id, parent=id)
        return r['data']
    except exceptions.TransportError, e:
        if e.status_code != 404:
            raise

def fetch_documents_by_task(idx, typ, query, taskname, field='body', full=True):
  """Query the task, return the documents"""
  child_type = _taskname_to_child_type(taskname, typ)
  query = {"has_child" : { 'type' : child_type, "query" : query } }
  return fetch_query_batch(idx, typ, query, field, full)

def fetch_results_by_document(idx, typ, query, taskname):
  """Query the document, return the results of the task"""
  child_type = _taskname_to_child_type(taskname, typ)
  query = {"has_parent" : { 'type' : typ, "query" : query } }
  return fetch_query_batch(idx, child_type, query, 'data')


# Copyright 2013-2015 Netherlands eScience Center and University of Amsterdam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Elasticsearch stuff."""

from __future__ import absolute_import
from datetime import datetime

from elasticsearch import Elasticsearch, client, exceptions
from elasticsearch.helpers import scan
from six import iteritems

from chardet import detect as chardetect

from ..core import app, _config


def _es():
    return Elasticsearch(hosts=_config['ELASTICSEARCH'])


_ES_DOC_FIELDS = ('index', 'type', 'id', 'field')


def es_document(idx, typ, id, field):
    """Returns a handle on a field in a document living in the ES store.

    This does not fetch the document, or even check that it exists.

    Parameters
    ----------
    idx : string
        ElasticSearch index.
    typ : string
        ElasticSearch type.
    id : string
        ElasticSearch document id.
    field : string
        Name of field.

    Returns
    -------
    An object of unspecified type representing the given field in the given
    document.
    """
    # Returns a dict instead of a custom object to ensure JSON serialization
    # works.
    return {'index': idx, 'type': typ, 'id': id, 'field': field}


def is_es_document(obj):
    """Returns True iff obj is an es_document."""
    return isinstance(obj, dict) and set(obj.keys()) == set(_ES_DOC_FIELDS)


def es_address(es_doc):
    """Returns the index, type, id and field of es_doc as a list.

    Parameters
    ----------
    es_doc : document handle created with es_document

    Returns
    -------
    A list of strings containing four objects, in order, the index, type,
    id and field of the document.
    """
    return [es_doc[dictfield] for dictfield in _ES_DOC_FIELDS]


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
    if is_es_document(doc):
        idx, typ, id, field = es_address(doc)
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

    Parameters
    ----------
    idx : string
        ElasticSearch index.
    typ : string
        ElasticSearch type.
    id : string
        ElasticSearch document id.
    field : string
        Name of field.

    Returns
    -------
    List of objects of whichever type were stored in the given field.

    Example
    -------
    >>> q = {"query_string": {"query": "hello"}}
    >>> r = fetch_query_batch("20news", "post", q, field="text")
    """
    hits = scan(_es(), {'query': query}, index=idx, doc_type=typ)
    return [hit['_source'][field] for hit in hits if field in hit['_source']]

CHECKED_MAPPINGS = set() #


def fetch_query_details_batch(idx, typ, query, full=True, tasknames=None):
    """Fetch all documents and their results matching query
        and return them as a list.

    Parameters
    ----------
    idx : string
        ElasticSearch index.
    typ : string
        ElasticSearch type.
    query : ElasticSearch query object
        ElasticSearch query describing the desired documents.
    full : bool
        Whether to return only the document (False) or the document and
        also any attached results (True).
    tasknames : list of string
        Return the document and the results of these tasks if available.
        Overrides full, i.e. if any task names are given, these are
        returned, even if full equals False.

    Returns
    -------
    Returns a list of (doc_id, ElasticSearch hit), one tuple for each document
    matching the query. If full is True or tasknames has been specified, each
    hit will have one additional key-value pair whose key is the name of the
    task, and whose value is the result of the task.
    """

    # since ES terminology is a bit confusing: a result here is a pair
    # (id, hit) where id is an ES document id, and hit is a dict with
    # keys _index, _type, _id, _score and _source.
    es_result = _es().search(index=idx, doc_type=typ, body={'query': query})
    results = [[hit['_id'], hit] for hit in es_result['hits']['hits']]
    if not full and not tasknames:
        return results

    # for full documents: make sure also the children are returned
    if not tasknames:
        tasknames = get_tasks_per_index(idx, typ)

    # HACK: one additional query per taskname!
    res_index = {doc_id: res_i for res_i, doc_id in enumerate([r[0] for r in results])}
    for taskname in tasknames:
        child_results = fetch_results_by_document(idx, typ, query, taskname)
        for child_id, child_hit in child_results:
            res_i = res_index[child_id]
            results[res_i][1][taskname] = child_hit['_source']['data']

    return results


def _check_parent_mapping(idx, child_type, parent_type):
    """
      Check that a mapping for the child_type exists
      Creates a new mapping with parent_type if needed
      This will fail horrifically if index1 is created and then deleted,
      because it will keep the index, child_type in memory.
    """
    if not (idx, child_type) in CHECKED_MAPPINGS:
        indices_client = client.indices.IndicesClient(_es())
        if not indices_client.exists_type(idx, child_type):
            body = {child_type: {"_parent": {"type": parent_type}}}
            indices_client.put_mapping(index=idx, doc_type=child_type,
                                       body=body)
        CHECKED_MAPPINGS.add((idx, child_type))


@app.task
def store_single(data, taskname, idx, typ, id):
    """Store the data as a child document.

    Parameters
    ----------
    data : object
        Some JSON-serializable object to store.
    taskname : string
        Name of the task that created the data.
    idx : string
        The ElasticSearch index to store the data under.
    typ : string
        The ElasticSearch type of the data.
    id : string
        The id of the parent document to store the data under.

    Returns
    -------
    Returns the data argument, unchanged.
    """
    child_type = _taskname_to_child_type(taskname, typ)
    _check_parent_mapping(idx, child_type, typ)
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
       Uses call on elastic search instead of the internal CHECKED_MAPPINGS to
       actually check the index.
    """
    try:
        indices_client = client.indices.IndicesClient(_es())
        r = indices_client.get_mapping(index=idx)[idx]
        tasks = set([])
        if 'mappings' not in r:
            return tasks
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


def fetch_documents_by_task(idx, typ, query, taskname, full=True):
    """Return documents with results for the given task"""
    child_type = _taskname_to_child_type(taskname, typ)
    query = {"has_child": {'type': child_type, "query": query}}
    return fetch_query_details_batch(idx, typ, query, full)


def fetch_results_by_document(idx, typ, query, taskname):
    """Return results of the given task for documents matching query"""
    child_type = _taskname_to_child_type(taskname, typ)
    query = {"has_parent": {'type': typ, "query": query}}
    return fetch_query_details_batch(idx, child_type, query, full=False)

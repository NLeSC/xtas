"""Elasticsearch stuff."""

from __future__ import absolute_import

from datetime import datetime

from elasticsearch import Elasticsearch

from ..celery import app

es = Elasticsearch()


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
        return es.get_source(index=idx, doc_type=typ, id=id)[field]
    else:
        # Assume simple string
        return doc


@app.task
def fetch_query_batch(idx, typ, query, field='body'):
    """Fetch all documents matching query and return them as a list.

    Returns a list of field contents, with documents that don't have the
    required field silently filtered out.
    """
    r = es.search(index=idx, doc_type=typ, body={'query': query},
                  fields=[field])
    r = (hit.get('fields', {}).get(field, None) for hit in r['hits']['hits'])
    return [hit for hit in r if hit is not None]


@app.task
def store_single(data, taskname, idx, typ, id):
    """Store the data in the xtas_results.taskname property of the document."""
    now = datetime.now().isoformat()
    doc = {"xtas_results": {taskname: {'data': data, 'timestamp': now}}}
    es.update(index=idx, doc_type=typ, id=id, body={"doc": doc})
    return data


def pipeline(doc, pipeline, store_final=True, store_intermediate=False, block=True):
    """
    Get the result for a given document. Pipeline should be a list of dicts, with members task and argument
    e.g. [{"module" : "tokenize"}, {"module" : "pos_tag", "arguments" : {"model" : "nltk"}}]
    @param block: if True, it will block and return the actual result. If False, it will return an AsyncResult
                  unless the result was cached, in which case it returns the result immediately (!)
    @param store_final: if True, store the final result
    @param store_intermediate: if True, store all intermediate results as well
    """
    def get_task(task_dict):
        "Create a celery task object from a dictionary with module and optional (kw)arguments"
        task = task_dict['module']
        if isinstance(task, (str, unicode)):
            task = app.tasks[task]
        args = task_dict.get('arguments')
        if isinstance(args, dict):
            return task.s(**args)
        elif args:
            return task.s(*args)
        else:
            return task.s()
    # form basic pipeline by resolving task dictionaries to task objects
    tasks = [get_task(t) for t in pipeline]
    
    if isinstance(doc, dict) and set(doc.keys()) == set(_ES_DOC_FIELDS):
        idx, typ, id, field = [doc[k] for k in _ES_DOC_FIELDS]
        chain = []
        input = None
        cache = get_xtas_results(idx, typ, id) 
        # Check cache for existing documents
        # Iterate over tasks in reverse order, check cached result, and otherwise
        # prepend task (and cache store command) to chain
        for i in range(len(tasks), 0, -1):
            taskname = "__".join(t.task for t in tasks[:i])
            if taskname in cache:
                input = cache[taskname]['data']
                break
            if (i == len(tasks) and store_final) or store_intermediate:
                chain.insert(0, store_single.s(taskname, idx, typ, id))
            chain.insert(0, tasks[i-1])
        if not chain:  # final result was cached, good!
            return input
        elif input is None:
            input = fetch(doc)
    else:
        # the doc is a string, so we can't use caching
        chain = tasks
        input = doc
    
    chain = celery.chain(*chain).delay(input)
    if block:
        return chain.get()
    else:
        return chain

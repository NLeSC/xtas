"""
Pipelining with partial caching
"""

import celery

from xtas.tasks.es import is_es_document, es_address
from xtas.tasks.es import get_single_result, store_single, fetch
from xtas.core import app


def pipeline(doc, pipeline, store_final=True, store_intermediate=False,
             block=True):
    """
    Get the result for a given document.
    Pipeline should be a list of dicts, with members task and argument
    e.g. [{"module" : "tokenize"},
          {"module" : "pos_tag", "arguments" : {"model" : "nltk"}}]
    @param block: if True, it will block and return the actual result.
                  If False, it will return an AsyncResult unless the result was
                  cached, in which case it returns the result immediately (!)
    @param store_final: if True, store the final result
    @param store_intermediate: if True, store all intermediate results as well
    """
    # form basic pipeline by resolving task dictionaries to task objects
    tasks = [_get_task(t) for t in pipeline]

    if is_es_document(doc):
        idx, typ, id, field = es_address(doc)
        chain = []
        input = None
        # Check cache for existing documents
        # Iterate over tasks in reverse order, check cached result, and
        # otherwise prepend task (and cache store command) to chain
        for i in range(len(tasks), 0, -1):
            taskname = "__".join(t.task for t in tasks[:i])
            input = get_single_result(taskname, idx, typ, id)
            if input:
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


def _get_task(task_dict):
    "Create a celery task object from a dictionary with module and arguments"
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

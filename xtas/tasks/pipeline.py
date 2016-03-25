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
    Pipeline should be a list of dicts, with members module and arguments
    e.g. [{"module" : "tokenize"},
          {"module" : "pos_tag", "arguments" : {"model" : "nltk"}}]
    @param block: if True, it will block and return the actual result.
                  If False, it will return an AsyncResult unless the result was
                  cached, in which case it returns the result immediately (!)
    @param store_final: if True, store the final result
    @param store_intermediate: if True, store all intermediate results as well
    """

    tasks = [_get_task(t) for t in pipeline]
    if is_es_document(doc):
        idx, typ, id, field = es_address(doc)

        def result_name(task_i):
            "Results are named after the task that created them"
            return "__".join(t.task for t in tasks[:(task_i + 1)])

        last_cached_result = None
        # we always have doc, which is result -1, the input to task 0
        last_cached_i = -1
        for task_i in reversed(range(0, len(tasks))):
            last_cached_result = get_single_result(result_name(task_i),
                                                   idx, typ, id)
            if last_cached_result:
                last_cached_i = task_i
                break

        if last_cached_i == -1:
            doc = fetch(doc)
        else:
            doc = last_cached_result

        new_tasks = []
        for task_i in range(last_cached_i + 1, len(tasks)):
            new_tasks.append(tasks[task_i])
            if (task_i == len(tasks) and store_final) or store_intermediate:
                new_tasks.append(store_single.s(result_name(task_i),
                                                idx, typ, id))
        tasks = new_tasks

    if not tasks:
        return doc

    chain = celery.chain(*tasks).delay(doc)
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

"""
Pipelining with partial caching
"""

import celery

from xtas.tasks.es import _ES_DOC_FIELDS, get_all_results, store_single, fetch
from xtas.celery import app


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

    if isinstance(doc, dict) and set(doc.keys()) == set(_ES_DOC_FIELDS):
        idx, typ, id, field = [doc[k] for k in _ES_DOC_FIELDS]
        chain = []
        input = None
        cache = get_all_results(idx, typ, id)
        # Check cache for existing documents
        # Iterate over tasks in reverse order, check cached result, and
        # otherwise prepend task (and cache store command) to chain
        for i in range(len(tasks), 0, -1):
            taskname = "__".join(t.task for t in tasks[:i])
            if taskname in cache:
                input = cache[taskname]
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
    if isinstance(task_dict, dict):
        task = task_dict['module']
        args = task_dict.get('arguments')
    else:
        task = task_dict
        args = None
    if isinstance(task, (str, unicode)):
        task = app.tasks[task]
    if isinstance(args, dict):
        return task.s(**args)
    elif args:
        return task.s(*args)
    else:
        return task.s()


if __name__ == '__main__':
    # provide a command line interface to pipelining
    # Maybe this should go to xtas.__main__ (?)
    # (or as xtas.pipeline)
    import argparse
    import sys
    import json

    from xtas.tasks.es import es_document
    from xtas.tasks import app


    epilog = '''The modules for the pipeline can be either the names of
                one or more modules, or a json string containing modules
                and arguments, e.g.:
                \'[{"module": "xtas.tasks.single.tokenize"},
                   {"module": "xtas.tasks.single.pos_tag"
                    "arguments": ["ntlk"]}]\'
            '''

    parser = argparse.ArgumentParser(epilog=epilog)

    parser.add_argument("module", nargs="+",
                        help="Name or json list of the module(s) to run")
    parser.add_argument("--always-eager", "-a", help="Don't use celery",
                        action="store_true")
    parser.add_argument("--id", "-i", help="ID of the document to process")
    parser.add_argument("--index", "-n", help="Elasticsearch index name")
    parser.add_argument("--doctype", "-d", help="Elasticsearch document type")
    parser.add_argument("--field", "-F", help="Elasticsearch field type")
    parser.add_argument("--input-file", "-f", help="Input document name. "
                        "If not given, use ID/index/doctype/field. "
                        "If neither are given, read document text from stdin")
    parser.add_argument("--output-file", "-o",
                    help="Output file. If not given, will write to stdout")
    args = parser.parse_args()

    # input
    if args.input_file is not None:
        doc = open(args.input_file).read()
    elif args.id is not None:
        doc = es_document(args.index, args.doctype, args.id, args.field)
    else:
        doc = sys.stdin.read()

    # pipeline
    if '[' in args.module[0] or '{' in args.module[0]:
        # json string
        pipe = json.loads(args.module[0])
    else:
        pipe = [{"module": m} for m in args.module]

    # output
    outfile = (open(args.output_file, 'w') if args.output_file is not None
               else sys.stdout)

    if args.always_eager:
        app.conf['CELERY_ALWAYS_EAGER'] = True

    result = pipeline(doc, pipe)
    json.dump(result, outfile, indent=2)

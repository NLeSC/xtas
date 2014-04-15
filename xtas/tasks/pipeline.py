"""
Pipelining with partial caching
"""

import celery

from xtas.tasks.es import _ES_DOC_FIELDS, get_all_results, store_single, fetch, get_multiple_results
from xtas.core import app


def pipeline_multiple(docs, pipe, store_final=True, store_intermediate=False):
    """
    Pipeline should be a list of dicts, with members task and argument
    e.g. [{"module" : "tokenize"},
          {"module" : "pos_tag", "arguments" : {"model" : "nltk"}}]
    @param store_final: if True, store the final result
    @param store_intermediate: if True, store all intermediate results as well
    @return: A list of results, not guaranteed to be in the same order as docs
    """

    def normalize_pipe(pipe):
        for task_dict in pipe:
            module = task_dict['module']
            if isinstance(module, (str, unicode)):
                module = app.tasks[module]
            yield dict(module=module, arguments=task_dict.get('arguments', {}))

    def get_chained_task(input, tasks, all_tasks, doc=None):
        """
        Get a celery task with the input and the chained tasks
        @param tasks: a list of dictionaries with 'module' and 'arguments']
        """
        head, tail = tasks[0], tasks[1:]
        # Apply result (cached value) to start of chain, add rest if needed
        head = head['module'].s(input, **head['arguments'])
        tail = [x['module'].s(**x['arguments']) for x in tail]
        chain = [head] + tail
        # Store final result
        if doc and store_final:
            taskname = "__".join(t['module'].name for t in all_tasks)
            chain.append(store_single.s(taskname, doc['index'], doc['type'], doc['id']))
        if doc and store_intermediate:
            for i in range(len(tasks)-1, 0, -1):
                taskname = "__".join(t['module'].name for t in all_tasks[:i])
                chain.insert(i, store_single.s(taskname, doc['index'], doc['type'], doc['id']))
        return celery.chain(*chain)

    tasks = list(normalize_pipe(pipe))

    todo = []
    cached = []

    str_docs = [doc for doc in docs if isinstance(doc, (str, unicode))]
    docs = [doc for doc in docs if not isinstance(doc, (str, unicode))]

    for i in range(len(tasks), 0, -1):
        if not docs:
            break
        unseen = []
        taskname = "__".join(t['module'].name for t in tasks[:i])
        for doc, result in get_multiple_results(docs, taskname):
            if result:
                chain = tasks[i:]
                if chain: # need to run one or more modules
                    todo.append(get_chained_task(result, chain, tasks, doc))
                else: # result is fully cached
                    cached.append(result)
            else:
                unseen.append(doc)
        docs = unseen

    for doc in docs:
        # not done at all
        input=fetch(doc)
        todo.append(get_chained_task(input, tasks, tasks, doc))
    for doc in str_docs:
        todo.append(get_chained_task(doc, tasks, tasks))

    # block on group get.
    # WARNING:This is not a good idea if the pipeline itself is made a task
    # Ideally I would just place 'results' and tasks together in a group, but is that possible?
    calc = celery.group(todo).apply_async().get() if todo else []

    return cached + calc

def pipeline(doc, pipeline, store_final=True, store_intermediate=False):
    """
    Get the result for a given document.
    """
    results = pipeline_multiple([doc], pipeline, store_final=store_final,
                                store_intermediate=store_intermediate)
    return results[0]


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

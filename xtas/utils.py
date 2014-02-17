from itertools import islice
from contextlib import contextmanager
from elasticsearch import Elasticsearch, client

@contextmanager
def clean_es(idx="xtas__unittest"):
    """
    Provide a clean elasticsearch instance for unittests. This *will* delete the given index!
    """
    # WvA: I would rather put it in tests, but I can't import tests from within the tests
    # (because stdlib tests takes precedence (?) and the tests are not loaded as packages in nose)
    es = Elasticsearch()
    indexclient = client.indices.IndicesClient(es)
    if indexclient.exists(idx):
        indexclient.delete(idx)
    indexclient.create(idx)
    try:
        yield idx, es
    finally:
        indexclient.delete(idx)
        

def batches(it, k):
    """Split iterable it into size-k batches.

    Returns
    -------
    batches : iterable
        Iterator over lists.
    """
    it = iter(it)
    while True:
        batch = list(islice(it, k))
        if not batch:
            break
        yield batch

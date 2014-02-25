from itertools import islice


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

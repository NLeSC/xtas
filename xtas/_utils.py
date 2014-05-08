from collections import Sequence
from itertools import islice

import nltk


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


def nltk_download(package):
    # XXX we could set the download_dir to download to xtas_data/nltk_data
    # and have everything in one place.
    nltk.download(package, raise_on_error=True, quiet=False)


def tosequence(it):
    """Convert iterable it to a sequence if it isn't already one."""
    return it if isinstance(it, Sequence) else list(it)

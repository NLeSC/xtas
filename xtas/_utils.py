from collections import Sequence

import nltk


_NLTK_DOWNLOADED = set()


def nltk_download(package):
    # XXX we could set the download_dir to download to xtas_data/nltk_data
    # and have everything in one place.
    if package not in _NLTK_DOWNLOADED:
        # Ensure we don't get a log message for *every single* successful
        # call, but we still log the actual downloads.
        # Should fix this upstream by allowing quiet='success' or something.
        nltk.download(package, raise_on_error=True, quiet=False)
        _NLTK_DOWNLOADED.add(package)


def tosequence(it):
    """Convert iterable it to a sequence if it isn't already one."""
    return it if isinstance(it, Sequence) else list(it)

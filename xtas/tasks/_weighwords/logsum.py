# Safe addition in log-space, taken from scikit-learn.
#
# Authors: G. Varoquaux, A. Gramfort, A. Passos, O. Grisel
# License: BSD

import numpy as np


def logsum(x):
    """Computes the sum of x assuming x is in the log domain.

    Returns log(sum(exp(x))) while minimizing the possibility of
    over/underflow.

    Examples
    ========

    >>> import numpy as np
    >>> a = np.arange(10)
    >>> np.log(np.sum(np.exp(a)))
    9.4586297444267107
    >>> logsum(a)
    9.4586297444267107
    """
    # Use the max to normalize, as with the log this is what accumulates
    # the less errors
    vmax = x.max(axis=0)
    out = np.log(np.sum(np.exp(x - vmax), axis=0))
    out += vmax
    return out

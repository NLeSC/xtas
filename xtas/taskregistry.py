"""Task registry singleton."""


# Task registry (singletons).
SYNC_TASKS = []
ASYNC_TASKS = []


def task(url, sync=False, methods=('GET',)):
    """Register f as a task (decorator).

    Parameters
    ----------
    path : string
        Path component of URL. Interpreted by Flask.
    sync : boolean, optional
        Whether the task is synchronous (executed on the web server frontend)
        or asynchronous (default, executed on worker nodes).
    methods : sequence, optional
        Allowed HTTP methods.
    """

    def wrap(f):
        global SYNC_TASKS, ASYNC_TASKS
        (SYNC_TASKS if sync else ASYNC_TASKS).append((f, url, methods))

        return f

    return wrap

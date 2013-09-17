"""Task registry singleton."""

from functools import wraps


TASKS = []      # Task registry (singleton)


def task(url):
    """Register f as a task (decorator)."""

    def wrap(f):
        global TASKS
        TASKS.append((f, url))

        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    return wrap

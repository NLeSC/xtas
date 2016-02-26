.. _overview:

Architecture overview
=====================

xtas can be used in one of three modes,
characterized by the following combinations of API and execution model:

* Python, standalone
* Python, distributed
* REST, distributed

In the first mode, xtas is simply a Python library of NLP tasks
that are called from your Python script or interactive interpreter,
and they are executed synchronously on your local machine.
Tasks are the functions listed in the :ref:`api`.

.. graphviz::

    digraph {
        rankdir=LR
        node [shape=rect, color=lightblue]

        "Python script" -> "xtas API"
    }

In the second mode, xtas workers run on some cluster (or a big machine),
and the local xtas library sends tasks to those workers
rather than executing them locally.
Tasks are submitted by calling tasks asynchronously::

    >>> result = xtas.tasks.guess_language.apply_async(['Welke taal zou dit zijn?'])
    >>> result
    <AsyncResult: 8b774f33-512e-41fe-90fa-33c09a7fc9c2>
    >>> result.get()
    ['nl', 0.999999995851766]

Tasks are distributed using `Celery <http://www.celeryproject.org>`_,
a Python wrapper around the RabbitMQ task queuing middleware.

.. graphviz::

    digraph {
        rankdir=LR
        node [shape=rect, color=lightblue]

        q [label="Task queue (Celery)"]

        "Python script" -> "xtas API"
        "xtas API" -> q
        q -> "xtas worker 1"
        q -> "xtas worker N"
    }

In the final mode, your code communicates with xtas workers through a
REST API that in turn communicates with the workers.

.. graphviz::

    digraph {
        rankdir=LR
        node [shape=rect, color=lightblue]

        rest [label="xtas REST API"]
        q [label="Task queue (Celery)"]

        "Program in any language" -> rest -> q
        q -> "xtas worker 1"
        q -> "xtas worker N"
    }

It follows that xtas consists of three parts:
a Python library, a worker program, and a web server program.
To :ref:`get started <setup>`, you only need the Python library and
no workers need to be running.
The web server is not need to use xtas from Python.

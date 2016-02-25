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

.. graphviz::

    digraph {
        rankdir=LR
        node [shape=rect, color=lightblue]

        "Python script" -> "xtas API"
    }

In the second mode, xtas workers run on some cluster (or a big machine),
and the local xtas library sends jobs to those workers
rather than executing them locally.

.. graphviz::

    digraph {
        rankdir=LR
        node [shape=rect, color=lightblue]

        q [label="Task queue (RabbitMQ)"]

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
        q [label="Task queue (RabbitMQ)"]

        "Program in any language" -> rest -> q
        q -> "xtas worker 1"
        q -> "xtas worker N"
    }

It follows that xtas consists of three parts:
a Python library, a worker program, and a web server program.
To get started, you only need the Python library and
no workers need to be running.

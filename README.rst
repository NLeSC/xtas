xtas
====

Distributed text analysis suite based on Celery.


Installation
------------

Set up a virtualenv and activate it, if desired. Then::

    pip install git+https://github.com/NLeSC/xtas.git

Next, make sure you have RabbitMQ running (currently only supported on
localhost).

If you've cloned xtas to a local directory and want to install from there
(maybe you've modified it), do::

    pip install git+file:///home/you/projects/xtas


Usage
-----

The xtas engine consists of two parts: a server that manages a task queue and
offers a ReST API, and a set of workers. Both need a configuration file to
work, which may be located anywhere in the file system. By default, both the
server and worker look for a file ``xtas.yaml`` in the current working
directory (i.e., the directory where they're started), so you need to generate
such a file. A template can be generated using::

    python -m xtas.configure > xtas.yaml

To start a server, do::

    python -m xtas.server

Similarly, to start a worker::

    python -m xtas.worker

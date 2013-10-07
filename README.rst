xtaslite
========

Distributed text analysis suite based on Celery.


Installation
------------

Set up a virtualenv and activate it, if desired. Then::

    pip install git+https://github.com/NLeSC/xtas.git

Next, make sure you have RabbitMQ running (currently only supported on localhost).


Usage
-----

The xtas engine consists of two parts: a server that manages a task queue and
offers a ReST API, and a set of workers. To start a server, do::

    python -m xtas.server

Similarly, to start a worker::

    python -m xtas.worker

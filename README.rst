xtaslite
========

Distributed text analysis suite based on Celery.

The xtas engine consists of two parts: a server that manages a task queue and
offers a ReST API, and a set of workers. To start a server, do::

    python -m xtas server

Similarly, to start a worker::

    python -m xtas worker

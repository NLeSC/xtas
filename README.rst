xtaslite
========

Distributed text analysis suite based on Celery.


Installation
------------

Use `pip <https://pypi.python.org/pypi/pip/1.1>` to install xtas from GitHub:

    pip install git+https://github.com/NLeSC/xtas.git


Getting started
---------------

You need to have RabbitMQ and Elasticsearch running. Then start a worker::

    celery -A xtas.tasks worker --loglevel=info

Start the web frontend::

    python -m xtas.webserver

Verify that it works by visiting::

    http://localhost:5000/tasks

You should see a list of supported tasks.

Now to perform some actual work, make sure Elasticsearch is populated with
documents, and visit a URL such as

    http://localhost:5000/run_es/morphy/blog/post/1/body

This runs the Morphy morphological analyzer on the "body" field of "post" 1
in ES index "blog". After some time, the results from Morphy are written to
this document, but in a field called "xtas_results".


Configuring
-----------
To override the built-in Celery configuration (which assumes, a.o., that
you're in the Amsterdam timezone), copy xtas/celeryconfig.py to a file
called xtas_celeryconfig.py in your PYTHONPATH and modify it. Note: the
file should not be in the xtas/ directory.

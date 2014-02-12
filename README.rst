xtas
====

Distributed text analysis suite based on Celery.

Copyright University of Amsterdam and Netherlands eScience Center, distributed
under the Apache License (see LICENSE.txt for details).


Installation
============

(Preferably) set up a virtualenv for xtas::

    virtualenv /some/where
    . /some/where/bin/activate

Use `pip <https://pypi.python.org/pypi/pip/1.1>` to install xtas from GitHub::

    pip install git+https://github.com/NLeSC/xtas.git


If the installation is taking a long time/fails to compile SciPy
----------------------------------------------------------------

While you can install xtas outside of a virtualenv, you can also set up one
that uses the system version of heavy dependencies. To do that, use your
favorite package manager (yum, apt, pip) to install NumPy, SciPy, NLTK and
scikit-learn, then::

    virtualenv --system-site-packages /some/where

and proceeds as described above.


Usage
=====


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


As a library
------------

To communicate with xtas from Python programs, import the ``tasks`` module in
your code and use the functions in that module::

    >>> import xtas.tasks
    >>> xtas.tasks.morphy("Hello, worlds!")
    ['Hello', ',', u'world', '!']

This runs the Morphy lemmatizer locally. To submit jobs to the job queue,
make sure it's running (you don't need the webserver for this) and use the
Celery calling conventions::

    >>> result = xtas.tasks.morphy.apply_async(["Hello, worlds!"])
    >>> result
    <AsyncResult: 97d6f0c0-79ed-4d8f-84ed-cf83f956eae4>
    >>> result.status
    u'SUCCESS'
    >>> result.get()
    [u'Hello', u',', u'world', u'!']

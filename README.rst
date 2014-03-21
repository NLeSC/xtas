xtas
====

Distributed text analysis suite based on Celery.

Copyright University of Amsterdam, Netherlands eScience Center and
contributors, distributed under the Apache License (see ``AUTHORS.txt``,
``LICENSE.txt``).


Installation
============

Make sure you have `Elasticsearch <http://www.elasticsearch.org/>`_ and
`RabbitMQ <http://www.rabbitmq.com/>`_ running. Installation instructions for
those can be found in various places. Make sure you have Python 2.6 or newer.

(Preferably) set up a virtualenv for xtas::

    virtualenv --system-site-packages /some/where
    . /some/where/bin/activate

The option ``--system-site-packages`` makes sure system NumPy, SciPy and NLTK
are used, if they are installed (recommended). Compiling these can take quite
a long time.

Use `pip <https://pypi.python.org/pypi/pip/1.1>`_ to install xtas.
To get the latest release::

    pip install xtas

To get the bleeding edge version from GitHub::

    pip install git+https://github.com/NLeSC/xtas.git


Usage
=====


Getting started
---------------

You need to have RabbitMQ and Elasticsearch running. On Debian/Ubuntu,
RabbitMQ can be installed with ``sudo apt-get install rabbitmq-server``.
See the `Elasticsearch website <http://www.elasticsearch.org/>`_ for how to
install that package if you don't already have it.

Then start an xtas worker::

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

You can now run the unittest suite using::

    nosetests -s -v --exe xtas

in the source directory (``pip install nose`` if needed). This requires a
running worker process and Elasticsearch. Running the tests first is a good
idea, because it will fetch some dependencies (e.g. NLTK models) that will
otherwise be fetched on demand.


Configuring
-----------

To override the built-in xtas configuration (which assumes that you're in the
Amsterdam timezone, have Elasticsearch at ``localhost:9200``, etc.), copy
``xtas/config.py`` to a file called ``xtas_config.py`` in your ``PYTHONPATH``
and modify it. Note: the file should not be in the ``xtas/`` directory.


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

The ``'SUCCESS'`` value for the ``status`` of the job means that it is
completed, so the ``get`` method will simply fetch the result from the queue.
A longer running job may report ``'PENDING'`` instead, in which case ``get``
will *block*, waiting for the job to complete.

You can now continue to the tutorial in ``doc/tutorial.rst``.


As a webservice
---------------

By default, the webserver listens to port 5000 on localhost *only*. Use the
``--host`` and `--port`` arguments to change this, e.g.::

    python -m xtas.webserver --host 0.0.0.0 --port 5001

to provide a public service to all the world (not recommended) on port 5001.


Frequently anticipated questions
--------------------------------

* If xtas downloads optional dependencies at runtime, where will it put those?

By default, in ``~/xtas_data``. You can override this by setting the
``XTAS_DATA`` environment variable.

* I can't run clustering/topic models/language models.

Look for ``extras_requires`` in ``setup.py`` for the packages to install.
If this says, e.g. ``gensim>=0.8``, do ``pip install -U gensim`` to install
the required package. (We're looking into ways to automate this.)

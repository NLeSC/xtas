.. _setup:

Getting started
===============

xtas can be run locally or on a cluster; the :ref:`overview` explains this
in more detail. This guide shows first how to get xtas running locally,
then how to run it as a distributed service.


Installation
------------

xtas runs on Linux (patches to support OS X are welcome).
It depends on Python 2.7, SciPy, the Java Runtime (JRE) and RabbitMQ.
On a Debian/Ubuntu/Linux Mint system, these dependencies can be installed with::

    sudo apt-get install libatlas-dev liblapack-dev rabbitmq-server \
        python-scipy openjdk-7-jre python-virtualenv build-essential \
        python-pip libxslt-dev

For CentOS/Fedora/Red Hat-style systems (this list is incomplete)::

    sudo yum install atlas-devel java-1.7.0-openjdk lapack-devel \
        libxslt-devel numpy python-devel rabbitmq-server scipy

(RabbitMQ is an `EPEL <https://fedoraproject.org/wiki/EPEL>`_ package.)

Next, set up a virtualenv for xtas::

    virtualenv --system-site-packages /some/where
    . /some/where/bin/activate

Use `pip <https://pypi.python.org/pypi/pip/1.1>`_ to install xtas.
To get the latest release::

    pip install xtas

To get the bleeding edge version from GitHub::

    pip install git+https://github.com/NLeSC/xtas.git

For installing from local source (if you want to modify xtas),
see :doc:`extending`.

Try it out in a Python shell::

    >>> from xtas.tasks import tokenize
    >>> tokenize("Hello, world!")
    [u'Hello', u',', u'world', u'!']

If you only want to use xtas as a library on your local machine, you're done.
Check the :ref:`api` for what xtas can do.


Distributed xtas
----------------

To run xtas in distributed mode, you need to have RabbitMQ
and, optionally, Elasticsearch running on some machine.
xtas by default assumes that these are running locally on their standard ports.
If they are not, run::

    python -m xtas.make_config

and edit the generated configuration file, ``xtas_config.py``,
to point xtas to RabbitMQ ``BROKER_URL`` (see `Celery configuration
<http://docs.celeryproject.org/en/latest/configuration.html>`_ for details)
and Elasticsearch.
Make sure this file is somewhere in your ``PYTHONPATH``
(test this with ``python -c 'import xtas_config'``).

Then start an xtas worker::

    python -m xtas.worker --loglevel=info &

If you want to use the xtas REST API, also start the webserver::

    python -m xtas.webserver &

Verify that it works::

    curl http://localhost:5000/tasks | python -m json.tool

You should see a list of supported tasks.

Now to perform some actual work, make sure Elasticsearch is populated with
documents, and visit a URL such as

    http://localhost:5000/run_es/morphy/20news/post/1/text

This runs the Morphy morphological analyzer on the "text" field of "post" 1
in ES index "20news". After some time, the results from Morphy are written to
a child document of this post, that can be obtained using::

    curl http://localhost:9200/20news/post__morphy/1?parent=1

You can now run the unittest suite using::

    python setup.py test

in the source directory (``pip install nose`` if needed). This requires a
running worker process and Elasticsearch. Running the tests first is a good
idea, because it will fetch some dependencies (e.g. NLTK models) that will
otherwise be fetched on demand.

To learn more about using xtas as a distributed text analysis engine,
see the :ref:`tutorial`.


Running as a service
--------------------

xtas can be run as a service on Linux. See the directory ``init.d`` in the
xtas source distribution for example init scripts.

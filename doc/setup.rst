Setting up xtas
===============


Installation
------------

Make sure you have `Elasticsearch <http://www.elasticsearch.org/>`_ and
`RabbitMQ <http://www.rabbitmq.com/>`_ running. Installation instructions for
those can be found in various places. Make sure you have Python 2.7 or newer.
Some tasks require a Java VM. xtas is primarily developed on Linux; OS X
support is not regularly tested, but issues/patches are welcome. Windows is
not supported.

TL;DR: ``pip install xtas``.

Long story: get the install dependencies, Python, pip, NumPy, Java (JRE).
On a Debian/Ubuntu/Linux Mint system, these can be installed with the package
manager, in which case it's a good idea to install other dependencies too
(so ``pip`` has to do less work)::

    sudo apt-get install rabbitmq-server python-scipy openjdk-7-jre \
        python-virtualenv build-essential python-pip libxslt-dev

For other systems, including Macs, getting SciPy through a Python distro
such as `Anaconda <http://continuum.io/downloads>`_ saves you the trouble
of setting up C, C++ and Fortran compilers.

Next, set up a virtualenv for xtas::

    virtualenv --system-site-packages /some/where
    . /some/where/bin/activate

The option ``--system-site-packages`` makes sure the system-wide NumPy, SciPy,
scikit-learn and NLTK are used, if they are pre-installed on the machine.
If you don't use this option, do make sure you ``pip install numpy``
before trying anything else.

Use `pip <https://pypi.python.org/pypi/pip/1.1>`_ to install xtas.
To get the latest release::

    pip install xtas

To get the bleeding edge version from GitHub::

    pip install git+https://github.com/NLeSC/xtas.git

For installing from local source, see :doc:`extending`.


Getting started
---------------

You need to have RabbitMQ and Elasticsearch running. On Debian/Ubuntu,
RabbitMQ can be installed with ``sudo apt-get install rabbitmq-server``.
See the `Elasticsearch website <http://www.elasticsearch.org/>`_ for how to
install that package if you don't already have it.

Then start an xtas worker::

    python -m xtas.worker --loglevel=info

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
Amsterdam timezone, have Elasticsearch at ``localhost:9200``, etc.), run::

    python -m xtas.make_config

to generate a file called ``xtas_config.py`` in the current directory. Change
this file as needed, make sure it is in the ``PYTHONPATH`` (*not* in the
``xtas/`` directory) and re-start the worker and webserver.

.. image:: https://api.travis-ci.org/NLeSC/xtas.png?branch=master
   :target: https://travis-ci.org/NLeSC/xtas

xtas
====

Distributed text analysis suite based on Celery.

Copyright University of Amsterdam, Netherlands eScience Center and
contributors, distributed under the Apache License (see ``AUTHORS.txt``,
``LICENSE.txt``). Parts of xtas use GPL-licensed software, such as the
Stanford NLP tools, and datasets that may incur additional restrictions.
Check the documentation for individual functions.


Quickstart
----------

Install::

    pip install xtas

Start worker::

    python -m xtas.worker --loglevel=info

Start web frontend::

    python -m xtas.webserver

For full documentation, please visit http://nlesc.github.io/xtas/.

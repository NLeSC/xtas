xtaslite
========

Distributed text analysis suite based on Celery.

Start a worker::

    celery -A xtas.tasks worker --loglevel=info

Start the web frontend::

    python rest.py

Verify that it works by visiting::

    http://localhost:5000/tasks

You should see a list of supported tasks.

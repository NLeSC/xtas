Frequently anticipated questions
================================

* If xtas downloads optional dependencies at runtime, where will it put those?

By default, in ``~/xtas_data``. You can override this by setting the
``XTAS_DATA`` environment variable.

In addition, xtas uses NLTK extensively, and that will download resource files
to ``~/nltk_data``.


* I get ``SystemError: error return without exception set`` when starting a
  Celery worker

Check if RabbitMQ is running and xtas is properly configured to talk to it.

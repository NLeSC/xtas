Modifying xtas
==============

This is a short guide to modifying xtas to suit specific needs
and (optionally) contributing code back.
It describes how to write now tasks and tie them in with the package.


Writing new tasks
-----------------

If you have a custom task that you want xtas to perform, then you can add it
as follows. Let's start with an example task that reverses a document,
character-by-character. Put the following in a file ``mytasks.py``::

    from xtas.celery import app

    @app.task
    def reverse(doc):
        return doc[::-1]

Make sure this file can be imported::

    $ python
    >>> from mytasks import reverse

If the above gave an error, adjust your ``PYTHONPATH``::

    export PYTHONPATH=.:$PYTHONPATH

Now adjust the xtas configuration. Run ``python -m xtas.make_config`` to get
a configuration file ``xtas_config.py`` in the current directory. At the bottom
of the file is an empty list called ``EXTRA_MODULES``. Put your module in it::

    EXTRA_MODULES = [
        'mytasks',
    ]

Now restart the worker. It should report ``mytasks.reverse`` as its first
task, followed by all the built-in tasks. You can now run your ``reverse``
function asynchronously, e.g. in a Python shell::

    >>> from mytasks import reverse
    >>> result = reverse.apply_async(["Hello, world!"])
    >>> result.get()
    u'!dlrow ,olleH'

If you also restart the webserver, you should see the new task in the list of
single-document tasks::

    $ curl -s http://localhost:5000/tasks | python -m json.tool | grep mytasks
        "mytasks.reverse",

To use the custom task from the REST API, e.g. with ``/run_es``, give its
fully qualified name (``mytasks.reverse``). Only built-in tasks have their
name abbreviated to not include the module name.

.. note::
   The webserver will currently assume your tasks is a single-document one,
   rather than a batch task. This is a known defect.


Contributing code
-----------------

If you have code that is reusable for others, and you want and are legally
capable of distributing it, then we're happy to consider it for inclusion in
xtas. Make sure you have copyright to the code you write or your employer
gives you permission to contribute under the terms of the Apache License
(``LICENSE.txt`` in the main source directory).

Fork the main repository on GitHub. Commit your changes to a separate branch.
Push this branch to GitHub and do a pull request. Your code will be reviewed
before pulling.

In the case of new tasks, put them in either ``xtas/tasks/single.py`` or
``xtas/tasks/cluster.py``, depending on the type of task. Follow the
conventions laid out in the docstrings of the modules. All xtas code should
conform to `PEP 8 <http://legacy.python.org/dev/peps/pep-0008/>`_, the style
guide for the Python standard library. Use the `pep8
<http://pep8.readthedocs.org/en/latest/>`_ and `pyflakes
<https://pypi.python.org/pypi/pyflakes>`_ tools to check code for compliance.
Also, be sure to use names starting with an underscore for private helper
functions.


Writing documentation
---------------------

Make sure to document your tasks.  Documentation is primarily written in the
form of docstrings, and we tend to follow the `NumPy docstring conventions
<https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_.

To tie docstrings into the HTML documentation, edit the ``api.rst`` file
in the directory ``doc``. To generate HTML, make sure you have Sphinx,
numpydoc and Celery 3.1.10 or later::

    pip install -U sphinx numpydoc celery sphinx_bootstrap_theme

then type ``make html`` inside the ``doc`` directory. HTML will be generated
in ``doc/_build/html``.

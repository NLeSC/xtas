Modifying xtas
==============

This is a short guide to modifying xtas and contributing code back.
It desribes how to write now tasks and tie them in with the package.

It is currently not easily possible to write a custom task that lives outside
of the xtas package proper.


Writing new tasks
-----------------

If you have a task that xtas has to perform but currently doesn't, then you
can add it as follows. Modify either ``xtas/tasks/single.py`` or
``xtas/tasks/cluster.py``, depending on the type of task. Follow the
conventions laid out in the docstrings of the modules.

All xtas code should conform to
`PEP 8 <http://legacy.python.org/dev/peps/pep-0008/>`_,
the style guide for the Python standard library.
Use the `pep8 <http://pep8.readthedocs.org/en/latest/>`_ and
`pyflakes <https://pypi.python.org/pypi/pyflakes>`_ tools
to check code for compliance.
Also, be sure to use names starting with an underscore for private helper
functions.


Writing documentation
---------------------

Documentation is primarily written in the form of docstrings.
We employ the `NumPy docstrings conventions
<https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_.

To tie docstrings into the HTML documentation, edit the ``.rst`` files
in the directory ``doc``. To generate HTML, make sure you have Sphinx,
numpydoc and Celery 3.1.10 or later::

    pip install -U sphinx numpydoc celery

then type ``make html`` inside the ``doc`` directory. HTML will be generated
in ``doc/_build/html``.


Contributing code back
----------------------

First, make sure you have copyright to the code you write or your employer
gives you permission to contribute under the terms of the Apache License
(``LICENSE.txt`` in the main source directory).

Fork the main repository on GitHub. Commit your changes to a separate branch.
Push this branch to GitHub and do a pull request. Your code will be reviewed
before pulling.

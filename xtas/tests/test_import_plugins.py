from nose.tools import assert_equal, assert_true

import os.path
from shutil import rmtree
import sys
from tempfile import mkdtemp

from xtas.taskregistry import ASYNC_TASKS
from xtas.util import import_plugins


def test_import_plugins():
    try:
        d = mkdtemp(prefix='xtastest')
        sys.path.append(os.path.dirname(d))

        l = len(ASYNC_TASKS)

        with open(os.path.join(d, '__init__.py'), 'w') as f:
            f.write('from xtas.taskregistry import task\n'
                    '@task()\n'
                    'def some_task(config):\n'
                    '    pass\n')

        config = {'main': {'plugins': os.path.basename(d)}}

        import_plugins(config)

        assert_equal(len(ASYNC_TASKS), l + 1)
        assert_true(any(x[0].__name__ == 'some_task' for x in ASYNC_TASKS))

    finally:
        sys.path.pop()
        rmtree(d, ignore_errors=True)

from __future__ import absolute_import

import importlib
import logging

from celery import Celery


__all__ = ['app']


logger = logging.getLogger(__name__)

app = Celery('xtas', include=['xtas.tasks'])
try:
    app.config_from_object('xtas_config.CELERY', force=True)
except ImportError:
    logger.warning('Cannot import xtas_config, falling back to default')
    app.config_from_object('xtas.config.CELERY', force=True)


# Import custom tasks (plugins)
try:
    from xtas_config import EXTRA_MODULES

    for m in EXTRA_MODULES:
        try:
            importlib.import_module(m)
        except ImportError as e:
            logger.error('ImportError for %r: %s' % (m, e))

except ImportError:     # no xtas_config
    pass


if __name__ == '__main__':
    app.start()

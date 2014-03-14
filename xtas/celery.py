from __future__ import absolute_import

import logging

from celery import Celery

logger = logging.getLogger(__name__)

app = Celery('xtas', include=['xtas.tasks'])
try:
    app.config_from_object('xtas_config.CELERY', force=True)
except ImportError:
    logger.warning('Cannot import celeryconfig, falling back to default')
    app.config_from_object('xtas.config.CELERY', force=True)

if __name__ == '__main__':
    app.start()

"""
Core functionality. Contains the configuration and the (singleton) Celery
"app" instance.
"""

from __future__ import absolute_import

import importlib
import logging

from celery import Celery

from . import _defaultconfig


__all__ = ['app', 'configure']


_config = {}

logger = logging.getLogger(__name__)

app = Celery('xtas', include=['xtas.tasks'])


def configure(config, import_error="raise", unknown_key="raise"):
    """Configure xtas. Settings made here override defaults and settings
    made in the configuration file.

    Parameters
    ----------
    config : dict
        Dict with keys ``CELERY``, ``ELASTICSEARCH`` and ``EXTRA_MODULES``
        will be used to configure the xtas Celery app.

        ``config.CELERY`` will be passed to Celery's ``config_from_object``
        with the flag ``force=True``.

        ``ELASTICSEARCH`` should be a list of dicts with at least the key
        'host'. These are passed to the Elasticsearch constructor (from the
        official client) unchanged.

        ``EXTRA_MODULES`` should be a list of module names to load.

        Failure to supply ``CELERY`` or ``ELASTICSEARCH`` causes the default
        configuration to be re-set. Extra modules will not be unloaded,
        though.

    import_error : string
        Action to take when one of the ``EXTRA_MODULES`` cannot be imported.
        Either "log", "raise" or "ignore".

    unknown_key : string
        Action to take when a member not matching the ones listed above is
        encountered in the config argument (except when its name starts
        with an underscore). Either "log", "raise" or "ignore".
    """

    members = {'CELERY', 'ELASTICSEARCH', 'EXTRA_MODULES'}

    if unknown_key != 'ignore':
        unknown_keys = set(config.keys()) - members
        if unknown_keys:
            msg = ("unknown keys %r found on config object %r"
                   % (unknown_keys, config))
            if unknown_keys == 'raise':
                raise ValueError(msg)
            else:
                logger.warn(msg)

    app.config_from_object(config.get('CELERY', 'xtas._defaultconfig.CELERY')) #
    es = config.get('ELASTICSEARCH', _defaultconfig.ELASTICSEARCH) #
    _config['ELASTICSEARCH'] = es
    logger.info('Using Elasticsearch at %s' % es)

    for m in config.get('EXTRA_MODULES', []):
        try:
            importlib.import_module(m)
        except ImportError as e:
            if import_error == 'raise':
                raise
            elif import_error == 'log':
                logger.warn(str(e))


try:
    config_module = importlib.import_module('xtas_config')
    content = {name: getattr(config_module, name)
               for name in dir(config_module)}
    configure(content, unknown_key='ignore')
except ImportError:
    logger.info('Cannot import xtas_config, falling back to default')
    configure({})

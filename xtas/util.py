"""Utility functions."""

from importlib import import_module


def getconf(config, key, default=None, error='default'):
    """Get value of key from the configuration tree config.

    Parameters
    ----------
    config : Mapping
        Configuration tree.
    key : string
        Name of option. Whitespace may be used to indicate a deeply nested
        option, e.g. "server port".
    default : object, optional
        Default value to be returned if key can't be found in config.
    error : string, optional
        What to do when a KeyError occurs: 'default' means return the default
        value, 'raise' means re-raise the exception.

    Examples
    --------
    >>> config = {'server': {'port': 5000, 'debug': True}}
    >>> getconf(config, 'server debug')
    True

    >>> config = {'worker': {}}
    >>> getconf(config, 'worker backend', default='amqp')
    'amqp'
    """
    try:
        for o in key.split():
            config = config[o]
    except KeyError:
        if error == 'default':
            return default
        else:
            raise KeyError('Key {} not found in configuration'.format(key))

    return config


def import_plugins(config):
    """Import plugins listed in the configuration object config.

    This imports the modules listed, which must be findable using sys.path.

    The plugins themselves should use the task decorator to register
    themselves.
    """
    # XXX allow appending to sys.path via the config file?
    modules = getconf(config, 'main plugins', ['xtas.plugins'])
    if isinstance(modules, basestring):
        modules = [modules]
    for m in modules:
        import_module(m)


def slashjoin(components):
    """Join a list of URL components with single slashes.

    Semanticizer in particular is picky about its urls:
    https://github.com/semanticize/semanticizer/issues/21
    """
    a = components.pop(0)
    z = components.pop(-1)

    return '/'.join([a.rstrip('/')] + components + [z.lstrip('/')])

"""Utility functions."""


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

"""Utility functions."""


def getconf(config, option, default=None):
    """Get value of option from the configuration tree config.

    Parameters
    ----------
    config : Mapping
        Configuration tree.
    option : string
        Name of option. Whitespace may be used to indicate a deeply nested
        option, e.g. "server port".
    default : object, optional
        Default value to be returned if option can't be found in config.

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
        for o in option.split():
            config = config[o]
    except KeyError:
        return default

    return config

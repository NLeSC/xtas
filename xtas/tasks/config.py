import simplejson as json

from ..taskregistry import task
from ..util import getconf


@task(sync=True, takes=None)
def config(config):
    if getconf(config, 'main debug'):
        return config
    else:
        raise ValueError('config only shown when "main debug" is true')

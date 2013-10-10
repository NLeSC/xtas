"""Task that always succeeds, for testing and debugging."""

import simplejson as json

from ..taskregistry import task
from ..util import getconf


@task('/test')
def test_task(config):
    return "success"


@task('/config')
def show_config(config):
    if getconf(config, 'main debug'):
        return json.dumps(config)
    else:
        raise ValueError('config only shown when "main debug" is true')

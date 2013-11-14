from __future__ import absolute_import

import langid
import requests

from ..taskregistry import task
from ..util import getconf, slashjoin


@task()
def run_langid(content, config):
    return langid.rank(content)

"""Elasticsearch-related stuff.

Effectively a proxy for Elasticsearch that redirects if configured to do so
(only enable when ES is not, e.g., firewalled).
"""

from functools import partial

from flask import request
import requests

from .taskregistry import task
from .util import getconf


estask = partial(task, sync=True)


@estask(methods=['GET', 'POST', 'PUT'])
def es(config, path):
    """Route Elasticsearch request through to ES."""

    es = getconf(config, 'main elasticsearch')

    url = '%s/%s' % (es, path)
    if getconf(config, 'server debug'):
        print('Forwarding to {!r}'.format(url))

    if request.query_string:
        url += "?%s" % request.query_string

    request.get_json(force=True)

    esreq = requests.Request(method=request.method, url=url,
                             headers=request.headers, data=request.data)
    resp = requests.Session().send(esreq.prepare())
    return (resp.text, resp.status_code, resp.headers)

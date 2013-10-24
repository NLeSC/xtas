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


@estask('/es/<string:index>/<string:type>/<string:id>',
        methods=['GET', 'POST', 'PUT'])
def es(config, index, type, id):
    """Route Elasticsearch request through to ES."""

    es = getconf(config, 'main elasticsearch')

    url = '%s/%s/%s/%s' % (es, index, type, id)
    if request.query_string:
        url += "?%s" % request.query_string

    esreq = requests.Request(method=request.method, url=url,
                             headers=request.headers, data=request.data)
    resp = requests.Session().send(esreq.prepare())
    return (resp.text, resp.status_code, resp.headers)

#!/usr/bin/env python

# Test script to fetch a set of documents from ES.

from __future__ import print_function
import json
import sys

from rawes import Elastic


def mget(hits):
    """Get documents from a list of hits (as returned by _query)."""

    return es.get('_mget', data={"docs": hits})


if len(sys.argv) != 2:
    print("usage: %s query" % sys.argv[0], file=sys.stderr)

query = sys.argv[1]

es = Elastic()
r = es.get("_search", data={"fields": "_id",
                            "query": {"query_string": {"query": query}}})
r = r["hits"]["hits"]
for hit in r:
    print(json.dumps(hit))

print(mget(r)['docs'][0]['_source'])

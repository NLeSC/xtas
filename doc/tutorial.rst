xtas tutorial
=============

Assuming you've properly configured and started xtas as described in the
README, here's how to do interesting work with it.

First, you need a document collection. If you don't have one already, download
the 20newsgroups dataset::

    curl http://qwone.com/~jason/20Newsgroups/20news-bydate.tar.gz | tar xzf -

Store the documents in Elasticsearch::

    >>> from elasticsearch import Elasticsearch
    >>> import os
    >>> from os.path import join
    >>> es = Elasticsearch()
    >>> files = (join(d, f) for d, _, fnames in os.walk('20news-bydate-train')
    ...          for f in fnames)
    ...
    >>> for i, f in enumerate(files):
    ...     body = {'text': open(f).read().decode('utf-8', errors='ignore')}
    ...     es.create(index='20news', doc_type='post', body=body, id=i)
    ...

Now, we can run named-entity recognition on the documents. Let's try it on one
document::

    >>> from xtas.tasks import es_document, stanford_ner_tag
    >>> doc = es_document('20news', 'post', 1, 'text')
    >>> tagged = stanford_ner_tag(doc)
    >>> [token for token, tag in tagged if tag == 'PERSON']
    ['Dane', 'C.', 'Butzer', 'Dane']

We just fetched the document from ES to run Stanford NER locally. That's not
the best we can do, so let's run it remotely. We can do so by running the
``stanford_ner_tag`` tasks asynchronously. First, observe that ``doc`` isn't
really the document: it's only a handle on the ES index::

    >>> doc
    {'index': '20news', 'type': 'post', 'id': 1, 'field': 'text'}

This handle can be sent over the wire to make Stanford NER run in the worker::

    >>> result = stanford_ner_tag.apply_async([doc])
    >>> result
    <AsyncResult: 44128ea3-970c-427c-80cc-2af499426b33>
    >>> [token for token, tag in result.get() if tag == 'PERSON']
    [u'Dane', u'C.', u'Butzer', u'Dane']

We have the same result, but now from a worker process. The ``result`` object
is an ``AsyncResult`` returned by Celery; see
`its documentation <http://docs.celeryproject.org/en/latest/>`_ for full
details.

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


Batch tasks
-----------

Some tasks require a batch of documents to work; an example is topic modeling.
Such tasks are available in the ``xtas.tasks.cluster`` package,
so named because most of the tasks can be considered a form of clustering.
Batches of documents are addressed using Elasticsearch queries,
which can be performed using xtas.
For example, to search for the word "hello" in the 20news collection::

    >>> from xtas.tasks.es import fetch_query_batch
    >>> hello = fetch_query_batch('20news', 'post',
    ...                           {'term': {'text': 'hello'}}, 'text')
    >>> len(hello)
    10

This fetches the ``'text'`` field of the documents that match the query.
(``'text'`` appears twice since you might want to match on the title,
but retrieve the body text, etc.)

Now we can fit a topic model to these document. (You need the gensim package
for this, ``pip install gensim``.) Try::

    >>> from xtas.tasks.cluster import lda
    >>> from pprint import pprint
    >>> pprint(lda(hello, 2))
    >>> pprint(lda(hello, 2))
    [[(u'and', 0.12790937338676811),
      (u'am', 0.1152182699301362),
      (u'any', 0.11363680997981712),
      (u'application', 0.10684945575768415),
      (u'algorithm', 0.10684176173416),
      (u'advance', 0.096258764014596071),
      (u'be', 0.089261082314667867),
      (u'anyone', 0.088502698282068443),
      (u'an', 0.087148958488685924),
      (u'ac', 0.068372826111416152)],
     [(u'and', 0.1150624380922104),
      (u'application', 0.11312568874979338),
      (u'anyone', 0.10728409178444523),
      (u'advance', 0.10695761539379559),
      (u'algorithm', 0.10218031622874352),
      (u'be', 0.10193138214362385),
      (u'any', 0.098412728034106681),
      (u'am', 0.097021607665297285),
      (u'an', 0.089350803758697001),
      (u'ac', 0.06867332814928688)]]

Here, the ``lda`` task returns (term, weight) pairs for two topics.
Admittedly, the topics aren't very pretty on this small set.

Of course, fetching the documents and running the topic model locally isn't
optimal use of xtas. Instead, let's set up a *chain* of tasks that runs the
query and fetches the results on a worker node, then runs the topic model
remotely as well. We'll use Celery syntax to accomplish this::

    >>> from celery import chain
    >>> fetch = fetch_query_batch.s('20news', 'post',
    ...                             {'term': {'text': 'hello'}}, 'text')
    >>> fetch_lda = chain(fetch, lda.s(k=2))    # make a chain
    >>> result = fetch_lda()                    # run the chain
    >>> pprint(result.get())                    # get results and display them
    [[[u'application', 0.11542413644453535],
      [u'am', 0.11459672375838384],
      [u'and', 0.11376035386021534],
      [u'algorithm', 0.11359529150248926],
      [u'advance', 0.10468087522675153],
      [u'be', 0.10361386971376114],
      [u'any', 0.10321250189311466],
      [u'anyone', 0.08927608350583244],
      [u'an', 0.08631073215334073],
      [u'ac', 0.055529431941575814]],
     [[u'and', 0.12924727078744289],
      [u'any', 0.1088955461011441],
      [u'anyone', 0.10640790208811389],
      [u'application', 0.10453772359410955],
      [u'advance', 0.09849716348992137],
      [u'am', 0.09774308133723099],
      [u'algorithm', 0.09546989905871668],
      [u'an', 0.09017462431916073],
      [u'be', 0.08754428312668586],
      [u'ac', 0.0814825060974741]]]

More details on creating chains can be found in the `Celery userguide
<http://celery.readthedocs.org/en/latest/userguide/canvas.html#chains>`_.

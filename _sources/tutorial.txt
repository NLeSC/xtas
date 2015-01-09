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


Storing results
---------------

We just saw how to run jobs remotely, fetching documents from an Elasticsearch
index. What is even more interesting is that we can also store results back to
ES, so we can use xtas as preprocessing for a semantic search engine.

We can use the ``store_single`` task to run NER on a document from the index
and store the result back, if we append it to our chain::

    >>> from celery import chain
    >>> from xtas.tasks.es import store_single
    >>> doc = es_document('20news', 'post', 3430, 'text')
    >>> ch = chain(stanford_ner_tag.s(doc, output="names"),
    ...            store_single.s('ner', doc['index'], doc['type'], doc['id']))
    >>> result = ch()
    >>> pprint(result.get())
    [[u'School of Computer Science', u'ORGANIZATION'],
     [u'McGill University Lines', u'ORGANIZATION'],
     [u'Sony', u'ORGANIZATION'],
     [u'SONY', u'ORGANIZATION'],
     [u'Invar Shadow Mask', u'ORGANIZATION'],
     [u'NEC', u'ORGANIZATION'],
     [u'NEC', u'ORGANIZATION'],
     [u'Tony', u'PERSON'],
     [u'McGill University', u'ORGANIZATION'],
     [u'Floyd', u'PERSON']]


``result.get()`` will now report the output from the NER tagger, but getting it
locally is not what we're after. The ``store_single`` task has also stored the
result back into the document, as you can verify with::

    >>> from xtas.tasks import get_all_results, get_single_result
    >>> pprint(get_all_results(doc['index'], doc['type'], doc['id']))
    {u'ner': [[u'Christopher Taylor', u'PERSON'],
              [u'Bradley University Distribution', u'ORGANIZATION'],
              [u'NHL', u'ORGANIZATION']],
    }
    >>> pprint(get_single_result('ner', doc['index'], doc['type'], doc['id']))
    [[u'Christopher Taylor', u'PERSON'],
     [u'Bradley University Distribution', u'ORGANIZATION'],
     [u'NHL', u'ORGANIZATION']]

``get_all_results`` returns all results for a document,
while ``get_single_result`` only returns the results for a specific taskname
(in our case specified as ``"ner"``).
But what if we had the task run forever ago and can't remember the tasks
that were run on a specific index?

::
    >>> pprint(get_tasks_per_index(doc['index'], doc['type']))
    set([u'ner'])

We can now actually query the xtas results.
Let's say we are interested in all documents that contain a PERSON name,
as identified by the named entity recognition::

    >>> from xtas.tasks import fetch_documents_by_task
    >>> query = {"match" : { "data" : {"query":"PERSON"}}}
    >>> pprint(fetch_documents_by_task('20news', 'post', query, 'ner', full=True))
    [[u'3430',
      {u'_id': u'3430',
       u'_index': u'20news',
       u'_score': 1.0,
       u'_source': {u'text': u"From: nittmo@camelot.bradley.edu (Christopher Taylor)\nSubject: Anyone Have Official Shorthanded Goal Totals?\nNntp-Posting-Host: camelot.bradley.edu\nOrganization: Bradley University\nDistribution: na\nLines: 4\n\nDoes anyone out there have the shorthanded goal totals of the NHL players\nfor this season?  We're trying to finish our rotisserie stats and need SHG\nto make it complete.\n\n"},
       u'_type': u'post',
       u'ner': [[u'Christopher Taylor', u'PERSON'],
                [u'Bradley University Distribution', u'ORGANIZATION'],
                [u'NHL', u'ORGANIZATION']]}]]

We now query only the results of the NER task!
The parameter ``full=True`` returns the full documents,
i.e., includes the results of the task as well.
The results of the xtas task are always stored in the ``data`` field:
make sure to take that into account when building your queries.

We can see that NHL is classified as an organisation.
What if we would like to query all occurences of NHL
to see if it is consistently classified as organisation?

::
    >>> from xtas.tasks import fetch_results_by_document
    >>> query = {"match" : { "text" : {"query":"NHL"}}}
    >>> pprint(fetch_results_by_document('20news', 'post', query, 'ner'))
    [[u'3430',
      {u'_id': u'3430',
       u'_index': u'20news',
       u'_score': 1.0,
       u'_source': {u'data': [[u'Christopher Taylor', u'PERSON'],
                              [u'Bradley University Distribution',
                               u'ORGANIZATION'],
                              [u'NHL', u'ORGANIZATION']],
                    u'timestamp': u'2014-12-18T10:57:37.259356'},
       u'_type': u'post__ner'}]]

Those two functions are convenience wrappers for the actual query function
``fetch_query_details_batch``:
here we can fire any elastic search query and get all results in a batch.
If we would want to have a simple query for all documents containing NHL,
we would say::

    >>> from xtas.tasks import fetch_query_details_batch
    >>> query = {"match" : { "text" : {"query":"NHL"}}}
    >>> pprint(fetch_query_details_batch('20news', 'post', query, True))
    [[u'3362',
      {u'_id': u'3362',
       u'_index': u'20news',
       u'_score': 0.8946465,
       u'_source': {u'text': u'From: mmilitzo@scott.skidmore.edu (matthew militzok)\nSubject: 1992 - 1993 FINAL NHL PLAYER STATS\nOrganization: Skidmo
    .... cut ....
    ]]

When multiple tasks were performed on the index,
``tasknames`` restricts the returned annotation results
to the ones in that list.

More complex queries can be built,
including relations between the between the different tasks and the documents.
Keep in mind that the type of a task is (currently)
a concatenation of the type of the original document and the taskname.
The query build to fetch a document by its task is then::

    >>> query = {'has_child': {'query': {'match': {'data': {'query': 'PERSON'}}}, 'type': 'post__ner'}}
    >>> pprint(fetch_query_details_batch('20news', 'post', query, True))
    [[u'3430',
      {u'_id': u'3430',
       u'_index': u'20news',
       u'_score': 1.0,
       u'_source': {u'text': u"From: nittmo@camelot.bradley.edu (Christopher Taylor)\nSubject: Anyone Have Official Shorthanded Goal Totals?\nNntp-Posting-Host: camelot.bradley.edu\nOrganization: Bradley University\nDistribution: na\nLines: 4\n\nDoes anyone out there have the shorthanded goal totals of the NHL players\nfor this season?  We're trying to finish our rotisserie stats and need SHG\nto make it complete.\n\n"},
       u'_type': u'post',
       u'ner': [[u'Christopher Taylor', u'PERSON'],
                [u'Bradley University Distribution', u'ORGANIZATION'],
                [u'NHL', u'ORGANIZATION']]}]]

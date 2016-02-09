.. xtas documentation master file, created by
   sphinx-quickstart on Wed Apr  2 14:39:31 2014.

.. raw:: html

	<div class="jumbotron">

xtas, the eXtensible Text Analysis Suite
========================================

This is the manual for xtas, a distributed text analysis package
based on Celery.
xtas provides NLP functionality such as named-entity recognition, parsing,
document clustering and topic models,
through Python (synchronous/asynchronous) and REST APIs.

xtas allows you to run distribute text analysis tasks over multiple machines.
But you can also use it as a fast extension/replacement
for existing packages such as NLTK.

xtas ties in with Elasticsearch.
You can use ES to store documents, then enrich them using xtas
The result of xtas analyses can go back into Elasticsearch,
so you can easily implement semantic search:
queries over named entities, sentiment analysis results, etc.

.. raw:: html

		<a href="setup.html" class="btn btn-primary btn-lg">Setup</a>
		<a href="tutorial.html" class="btn btn-primary btn-lg">Tutorial</a>
		<a href="api.html" class="btn btn-primary btn-lg">API</a>
	</div>

Contents
========

.. toctree::
   :maxdepth: 2

   setup
   tutorial
   api
   rest
   extending
   changelog
   faq


Developed by
============

.. TODO find a better way of displaying these (in the theme?)

.. raw:: html

	<div class="col-md-6">
		<a href="http://esciencecenter.nl">
			<img src="_static/logo_nlesc.png" title="Netherlands eScience Center" />
		</a>
	</div><div class="col-md-6" style="padding-top:6px;">
		<br /><br />
		<a href="http://ilps.science.uva.nl">
			<img src="_static/logo_uva.png" title="ILPS, University of Amsterdam" />
		</a>
	</div>


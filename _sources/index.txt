.. xtas documentation master file, created by
   sphinx-quickstart on Wed Apr  2 14:39:31 2014.

.. raw:: html

	<div class="jumbotron">

xtas, the eXtensible Text Analysis Suite
========================================

xtas is a collection of natural language processing and text mining tools,
brought together in a single software package
with built-in distributed computing
and support for the Elasticsearch document store.

xtas functionality consists partly of wrappers for existing packages,
with automatic installation of software and data;
and partly of custom-built modules coming out of research.
Currently offered are various parsers for Dutch and English
(Alpino, CoreNLP, Frog, Semafor),
named entity recognizers (Frog, Stanford and custom-built ones),
a temporal expression tagger (Heideltime)
and a sentiment tagger based on SentiWords.

A basic installation of xtas works like a Python module.
Built-in package management and a simple, uniform interface
take away the hassle of installing, configuring and using
many existing NLP tools.

xtas's open architecture makes it possible to include custom code,
run this in a distributed fashion and have it communicate with Elasticsearch
to provide document storage and retrieval.
See :ref:`extending` for details.

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


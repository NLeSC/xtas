Changelog/release notes
=======================

3.0
---

xtas 3.0 is a complete rewrite of the University of Amsterdam's xTAS system
(retroactively, xtas 2) and its predecessor, Fietstas (xtas 1). No attempt
has been made to retain backward compatibility, so that code could be
redesigned in a clean, simple, scalable way.

Features introduced in xtas 3 include:

* Communication with Elasticsearch
* REST API to single-document tasks
* Python API for both synchronous and asynchronous execution (with Celery)

And the following NLP tasks:

* Tokenization, based on NLTK
* Named-entity recognition with Stanford NER (``stanford_ner_tag``)
* Wrapper for the Frog Dutch POS tagger/NER tagger/dependency parser
* Wrapper for the Alpino parser for Dutch
* Language guessing
* English lemmatization with morphy
* Movie review polarity classification
* English POS tagging with NLTK
* Wrapper for the Semafor semantic parser
* Word-level sentiment polarity tagging with SentiWords
* Document clustering with :math:`k`-means (``kmeans``, ``big_kmeans``)
* Topic modeling with latent semantic analysis (LSA), latent dirichlet
  allocation (LDA), based on scikit-learn and Gensim
* Parsimonious language modeling, useful for discriminative word clouds

Preliminary versions of 3.0 were named 2.99.

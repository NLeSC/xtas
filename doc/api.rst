.. _api:

API reference
=============

xtas.core
---------

.. automodule:: xtas.core

.. autofunction:: configure


xtas.tasks.single
-----------------

.. automodule:: xtas.tasks.single

.. It seems we have to list all the tasks here. automodule doesn't pick them
   up, probably because of the decorator.

.. autotask:: alpino
.. autotask:: corenlp
.. autotask:: corenlp_lemmatize
.. autotask:: dbpedia_spotlight
.. autotask:: frog
.. autotask:: guess_language
.. autotask:: morphy
.. autotask:: movie_review_polarity
.. autotask:: pos_tag
.. autotask:: semafor
.. autotask:: semanticize
.. autotask:: sentiwords_tag
.. autotask:: stanford_ner_tag
.. autotask:: stem_snowball
.. autotask:: tokenize
.. autotask:: untokenize


xtas.tasks.cluster
------------------

.. automodule:: xtas.tasks.cluster

.. autotask:: big_kmeans
.. autotask:: kmeans
.. autotask:: lda
.. autotask:: lsa
.. autotask:: parsimonious_wordcloud

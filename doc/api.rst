API reference
=============

xtas.core
---------

.. automodule:: xtas.core


xtas.tasks.single
-----------------

.. automodule:: xtas.tasks.single

.. It seems we have to list all the tasks here. automodule doesn't pick them
   up, probably because of the decorator.

.. autotask:: morphy
.. autotask:: movie_review_polarity
.. autotask:: pos_tag
.. autotask:: stanford_ner_tag
.. autotask:: semanticize
.. autotask:: sentiwords_tag
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

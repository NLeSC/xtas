# Simple example of how to construct a pipeline of operations from Python
# and apply them to an ES document, storing the result back into ES.

from celery import chain
from xtas.tasks.es import es_document, store_single
from xtas.tasks.single import pos_tag, tokenize

doc = es_document('blog', 'post', 1, 'body')

# The following is Celery syntax for a pipeline of operations.
ch = chain(tokenize.s(doc)
           | pos_tag.s('nltk')
           | store_single.s('pipeline', 'blog', 'post', 1)
           )

r = ch.delay()
print(r.get())

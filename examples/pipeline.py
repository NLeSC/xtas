# Simple example of how to construct a pipeline of operations from Python
# and apply them to an ES document, storing the result back into ES.

from celery import chain
from xtas.tasks import *

ch = chain(fetch_es.s('blog', 'post', 1, 'body')
           | tokenize.s() | pos_tag.s('nltk')
           | store_single.s('pipeline', 'blog', 'post', 1)
          )

r = ch.delay()
print(r.get())

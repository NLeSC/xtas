#from celery.signals import worker_process_init

import os.path

_TABLE = {}
_MAX_LEN = 0

_SENTI_PATH = os.path.join(os.path.dirname(__file__), "sentiwords.txt")


#@worker_process_init.connect
def load():
    max_len = 0           # max n-gram length
    sentiment = {}
    with open(_SENTI_PATH) as f:
        for ln in f:
            if ln.startswith('#'):
                continue

            w, prior = ln.rsplit('\t', 1)
            prior = float(prior)
            if prior == 0:
                continue

            max_len = max(max_len, w.count(' '))
            sentiment[w] = prior

    global _TABLE
    global _MAX_LEN
    _TABLE = sentiment
    _MAX_LEN = max_len


load()


def tag(words):
    def try_position(k):
        for j in xrange(_MAX_LEN, 0, -1):
            ngram = ' '.join(words[i:i+j])
            try:
                return j, ngram, _TABLE[ngram]
            except KeyError:
                pass

    i = 0
    while i < len(words):
        try:
            skip, ngram, polarity = try_position(i)
            yield ngram, polarity
            i += skip
        except TypeError:
            yield words[i], 0
            i += 1

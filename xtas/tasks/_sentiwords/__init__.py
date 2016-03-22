#from celery.signals import worker_process_init

import os.path

_TABLE = {}
_MAX_LEN = 0

_SENTI_PATH = os.path.join(os.path.dirname(__file__), "sentiwords.txt")


#@worker_process_init.connect
def load():
    max_len = 0           # max n-gram length minus one
    sentiment = {}
    with open(_SENTI_PATH) as sentiwords_file:
        for line in sentiwords_file:
            if line.startswith('#'):
                continue

            word, prior = line.split('\t')
            prior = float(prior)

            max_len = max(max_len, word.count(' '))
            sentiment[word] = prior

    global _TABLE
    global _MAX_LEN
    _TABLE = sentiment
    _MAX_LEN = max_len


load()


def tag(words):
    def longest_ngram_at(k):
        for j in xrange(_MAX_LEN, 0, -1):
            ngram = ' '.join(words[k:k+j])
            if ngram in _TABLE:
                return j, ngram, _TABLE[ngram]
        return 1, words[i], 0

    i = 0
    while i < len(words):
        skip, ngram, polarity = longest_ngram_at(i)
        yield ngram, polarity
        i += skip

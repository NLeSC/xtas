# Copyright 2013-2015 Netherlands eScience Center and University of Amsterdam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#from celery.signals import worker_process_init

import os.path

_TABLE = {}
_MAX_LEN = 0

_SENTI_PATH = os.path.join(os.path.dirname(__file__), "sentiwords.txt")


#@worker_process_init.connect
def load():
    """Loads SentiWords file and builds lookup table from it."""
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
    """Add polarity tags to a list of words.

    This function uses the SentiWords lexicon to add prior polarity tags to
    the given list of words.

    Parameters
    ----------
    words: sequence of strings, each containing one word

    Returns
    -------
    This function generates (ngram, polarity) pairs, where ngram is one or
    more concatenated words, and polarity is the prior polarity, in the
    range [-1, 1]. The concatenated ngrams together equal the original text.
    """
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

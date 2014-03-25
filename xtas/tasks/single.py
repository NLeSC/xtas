"""Embarrasingly parallel (per-document) tasks."""

from __future__ import absolute_import

import json
from urllib import urlencode
from urllib2 import urlopen

import nltk

from .es import fetch
from ..celery import app


@app.task
def morphy(doc):
    """Lemmatize tokens using morphy, WordNet's lemmatizer."""
    # XXX Results will be better if we do POS tagging first, but then we
    # need to map Penn Treebank tags to WordNet tags.
    nltk.download('wordnet', quiet=False)
    return map(nltk.WordNetLemmatizer().lemmatize,
               _tokenize_if_needed(fetch(doc)))


@app.task
def movie_review_polarity(doc):
    """Returns the probability that the movie review doc is positive."""
    from ._polarity import classify
    return classify(doc)


def _tokenize_if_needed(s):
    if isinstance(s, basestring):
        # XXX building token dictionaries is actually wasteful...
        return [tok['token'] for tok in tokenize(s)]
    return s


@app.task
def stanford_ner_tag(doc, format="tokens"):
    """Named entity recognizer using Stanford NER.

    Currently only supports the model 'english.all.3class.distsim.crf.ser.gz'.

    Parameters
    ----------
    doc : document
        Tokenization will be done by Stanford NER using its own rules.

    format : string, optional
        Output format. "tokens" gives a list of (token, nerclass) triples,
        similar to the IO format but without the "I-". "names" returns a list
        of (name, class pairs); since Stanford NER does not distinguish between
        start and continuation of name spans, the reconstruction of full names
        is heuristic.

    Returns
    -------
    tagged : list of list of pair of string
        For each sentence, a list of (word, tag) pairs.
    """
    from ._stanford_ner import tag
    doc = fetch(doc)
    return tag(doc, format)


@app.task
def pos_tag(tokens, model='nltk'):
    """Perform part-of-speech (POS) tagging.

    Currently only does English using the default model in NLTK.

    Expects a list of tokens.
    """
    if model != 'nltk':
        raise ValueError("unknown POS tagger %r" % model)
    nltk.download('maxent_treebank_pos_tagger')
    return nltk.pos_tag([t["token"] for t in tokens])


@app.task
def sentiwords_tag(doc, output="bag"):
    """Tag doc with SentiWords polarity priors.

    Performs left-to-right, longest-match annotation of token spans with
    polarities from SentiWords.

    Uses no part-of-speech information; when a span has multiple possible
    taggings in SentiWords, the mean is returned.

    Parameters
    ----------
    doc : document or list of strings

    output : string, optional
        Output format. Either "bag" for a histogram (dict) of annotated token
        span frequencies, or "tokens" a mixed list of strings and (list of
        strings, polarity) pairs.
    """
    from ._sentiwords import tag
    doc = _tokenize_if_needed(fetch(doc))

    tagged = tag(doc)
    if output == "bag":
        d = {}
        for i, j, ngram, polarity in tagged:
            if ngram in d:
                d[ngram][1] += 1
            else:
                d[ngram] = [polarity, 1]
        return d

    elif output == "tokens":
        out = []
        i = 0
        for j, k, ngram, polarity in tagged:
            out.extend(doc[i:j])
            out.append((ngram, polarity))
            i = k - 1
        out.extend(doc[i:])
        return out

    else:
        raise ValueError("unknown output format %r" % output)


@app.task
def tokenize(doc):
    """Tokenize text.

    Uses the NLTK function word_tokenize.
    """
    text = fetch(doc)
    return [{"token": t} for t in nltk.word_tokenize(text)]


@app.task
def semanticize(doc, lang='en'):
    """Run text through the UvA semanticizer.

    Calls the UvA semanticizer webservice to perform entity linking and
    returns the names/links it has found.

    See http://semanticize.uva.nl/ for details.
    """
    text = fetch(doc)

    if not lang.isalpha():
        raise ValueError("not a valid language: %r" % lang)
    url = 'http://semanticize.uva.nl/api/%s?%s' % (lang,
                                                   urlencode({'text': text}))
    return json.loads(urlopen(url).read())['links']


@app.task
def untokenize(tokens):
    """Undo tokenization.

    Simply concatenates the given tokens with spaces in between. Useful after
    tokenization and filtering.
    """
    return ' '.join(tokens)

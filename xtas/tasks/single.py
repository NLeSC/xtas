"""Single-document tasks.

These tasks process one document at a time. Usually, a document is passed as
the first argument; it may either be a string or the result from
``xtas.tasks.es.es_document``, which is a reference to a document in the
Elasticsearch store.
"""

from __future__ import absolute_import

import json
from urllib import urlencode
from urllib2 import urlopen

import nltk

from .es import fetch
from ..core import app
from .._utils import nltk_download


@app.task
def guess_language(doc, output="best"):
    """Guess the language of a document.

    Uses the langid library.

    Parameters
    ----------
    doc : document

    output : string
        Either "best" to get a pair (code, prob) giving the two-letter code
        of the most probable language and its probability, or "rank" for a
        list of such pairs for all languages in the model.
    """
    from langid import classify, rank

    try:
        func = {"best": classify, "rank": rank}[output]
    except KeyError:
        raise ValueError("invalid parameter value output=%r" % output)

    return func(fetch(doc))


@app.task
def morphy(doc):
    """Lemmatize tokens using morphy, WordNet's lemmatizer.

    No part-of-speech tagging is done.

    Returns
    -------
    lemmas : list
        List of lemmas.
    """
    # XXX Results will be better if we do POS tagging first, but then we
    # need to map Penn Treebank tags to WordNet tags.
    nltk_download('wordnet')
    return map(nltk.WordNetLemmatizer().lemmatize,
               _tokenize_if_needed(fetch(doc)))


@app.task
def movie_review_polarity(doc):
    """Movie review polarity classifier.

    Runs a logistic regression model trained on a set of positive and negative
    movie reviews (all in English).

    Returns
    -------
    p : float
        The probability that the movie review ``doc`` is positive.
    """
    from ._polarity import classify
    return classify(doc)


def _tokenize_if_needed(s):
    if isinstance(s, basestring):
        # XXX building token dictionaries is actually wasteful...
        return [tok['token'] for tok in tokenize(s)]
    return s


@app.task
def stanford_ner_tag(doc, output="tokens"):
    """Named entity recognizer using Stanford NER.

    Currently only supports the model 'english.all.3class.distsim.crf.ser.gz'.

    Parameters
    ----------
    doc : document
        Tokenization will be done by Stanford NER using its own rules.

    output : string, optional
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
    return tag(doc, output)


@app.task
def pos_tag(tokens, model='nltk'):
    """Perform part-of-speech (POS) tagging.

    Currently only does English using the default model in NLTK.

    Expects a list of tokens.
    """
    if model != 'nltk':
        raise ValueError("unknown POS tagger %r" % model)
    nltk_download('maxent_treebank_pos_tagger')
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
        for ngram, polarity in tagged:
            if polarity == 0:
                continue
            if ngram in d:
                d[ngram][1] += 1
            else:
                d[ngram] = [polarity, 1]
        return d

    elif output == "tokens":
        return [ngram if polarity == 0 else (ngram, polarity)
                for ngram, polarity in tagged]

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

    See http://semanticize.uva.nl/doc/ for details.

    References
    ----------
    M. Guerini, L. Gatti and M. Turchi (2013). "Sentiment analysis: How to
    derive prior polarities from SentiWordNet". Proc. EMNLP, pp. 1259-1269.

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

    Returns
    -------
    doc : string
    """
    return ' '.join(tokens)


@app.task
def frog(doc, output='raw'):
    """
    Run a document through the frog server at localhost:9887
    If output is 'raw', returns the raw output lines.
    If output is 'tokens', returns dictionaries for the tokens
    If output is 'saf', returns a SAF dictionary
    """
    from .frog import call_frog, parse_frog, frog_to_saf
    if output not in ('raw', 'tokens', 'saf'):
        raise ValueError("Uknown output: {output}, "
                         "please choose either raw, tokens, or saf"
                         .format(**locals()))
    text = fetch(doc)
    result = call_frog(text)
    if output == 'raw':
        return list(result)
    if output in ('tokens', 'saf'):
        result = parse_frog(result)
        if output == 'tokens':
            return list(result)
        return frog_to_saf(result)

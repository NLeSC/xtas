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
import spotlight

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
def dbpedia_spotlight(doc, lang='en', conf=0.5, supp=0, api_url=None):
    """Run text through a DBpedia Spotlight instance.

    Calls the DBpedia Spotlight instance to perform entity linking and
    returns the names/links it has found.

    See http://spotlight.dbpedia.org/ for details.
    This task uses a Python client for DBp Spotlight:
    https://github.com/aolieman/pyspotlight
    """
    text = fetch(doc)

    endpoints_by_language = {
        'en': "http://spotlight.sztaki.hu:2222/rest",
        'de': "http://spotlight.sztaki.hu:2226/rest",
        'nl': "http://spotlight.sztaki.hu:2232/rest",
        'fr': "http://spotlight.sztaki.hu:2225/rest",
        'it': "http://spotlight.sztaki.hu:2230/rest",
        'ru': "http://spotlight.sztaki.hu:2227/rest",
        'es': "http://spotlight.sztaki.hu:2231/rest",
        'pt': "http://spotlight.sztaki.hu:2228/rest",
        'hu': "http://spotlight.sztaki.hu:2229/rest",
        'tr': "http://spotlight.sztaki.hu:2235/rest"
    }

    no_coref_filter = {
        'coreferenceResolution': False
    }

    if lang not in endpoints_by_language and not api_url:
        raise ValueError("Not a valid language code: %r" % lang)

    if not api_url:
        api_url = endpoints_by_language[lang]

    api_url += "/candidates"

    try:
        spotlight_resp = spotlight.candidates(
            api_url, text,
            confidence=conf,
            support=supp,
            spotter='Default',
            filters=no_coref_filter
        )
    except (spotlight.SpotlightException, TypeError) as e:
        return {'error': e.message}

    for annotation in spotlight_resp:
        if u'resource' in annotation:
            if isinstance(annotation[u'resource'], dict):
                annotation[u'resource'] = [annotation[u'resource']]

    return spotlight_resp
"""Single-document tasks.

These process one document per function call (in Python) or REST call (via
the web server, ``/run`` or ``/run_es``). Most single-document tasks take a
document as their first argument. In the Python interface this may either be
a string or the result from ``xtas.tasks.es.es_document``, a reference to a
document in an Elasticsearch store.
"""

from __future__ import absolute_import

import json

from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen

from cytoolz import identity, pipe
import nltk
import spotlight

from .es import fetch
from ..core import app
from .._utils import nltk_download


@app.task
def guess_language(doc, output="best"):
    """Guess the language of a document.

    This function applies a statistical method to determine the language of a
    document. Depending on the ``output`` argument, it may either return a
    single language code, or a ranking of languages that a document may be
    written in, sorted by probability.

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

    return pipe(doc, fetch, func)


@app.task
def heideltime(doc, language='english'):
    """Runs the Heideltime temporal tagger on the document doc.

    Returns the text of doc with temporal expressions marked up in the TIMEX
    format.
    """
    from ._heideltime import call_heideltime

    # TODO Add an option to parse the TIMEX XML format.
    return call_heideltime(fetch(doc), language)


@app.task
def morphy(doc):
    """Lemmatize tokens using morphy, WordNet's lemmatizer.

    Finds the morphological root of all words in ``doc``, which is assumed to
    be written in English.

    Returns
    -------
    lemmas : list
        List of lemmas.

    See also
    --------
    stem_snowball: simpler approach to lemmatization (stemming).
    """
    # XXX Results will be better if we do POS tagging first, but then we
    # need to map Penn Treebank tags to WordNet tags.
    nltk_download('wordnet')
    tokens = pipe(doc, fetch, _tokenize_if_needed)
    return map(nltk.WordNetLemmatizer().lemmatize, tokens)


@app.task
def movie_review_emotions(doc):
    """Emotion (fine-grained sentiment) tagger for movie reviews.

    The training data for this function is that of Buitinck et al., with the
    training and test data concatenated. The algorithm is SVMs in a binary
    relevance (one-vs-rest) combination.

    Returns
    -------
    tagged : list of (string, list of string)
        A list of (sentence, labels) pairs. Each sentence may have zero or
        more labels.

    References
    ----------
    L. Buitinck, J. van Amerongen, E. Tan and M. de Rijke (2015).
    Multi-emotion detection in user-generated reviews. Proc. ECIR.
    https://staff.fnwi.uva.nl/m.derijke/wp-content/papercite-data/pdf/buitinck-multi-emotion-2015.pdf
    """
    from ._emotion import classify
    nltk_download('punkt')
    sentences = pipe(doc, fetch, nltk.sent_tokenize)
    return list(zip(sentences, classify(sentences)))


@app.task
def movie_review_polarity(doc):
    """Movie review polarity classifier.

    Determines whether the film review ``doc`` is positive or negative. Might
    be applicable to other types of document as well, but uses a statistical
    model trained on a corpus of user reviews of movies, all in English.

    Returns
    -------
    p : float
        The probability that the movie review ``doc`` is positive.

    See also
    --------
    movie_review_emotions: per-sentence fine-grained sentiment tagger

    sentiwords_tag: more generic sentiment expression tagger
    """
    from ._polarity import classify
    return pipe(doc, fetch, classify)


def _tokenize_if_needed(s):
    return tokenize(s) if isinstance(s, basestring) else s


@app.task
def nlner_conll(doc):
    """Baseline NER tagger for Dutch, based on the CoNLL'02 dataset.

    See http://www.clips.uantwerpen.be/conll2002/ner/ for the dataset and
    its license.

    See also
    --------
    frog: NER tagger and dependency parser for Dutch.

    stanford_ner_tag: NER tagger for English.
    """
    from ._nl_conll_ner import ner
    return pipe(doc, fetch, _tokenize_if_needed, ner)


@app.task
def stem_snowball(doc, language):
    """Stem words in doc using the Snowball stemmer.

    Set the parameter ``lang`` to a language code such as "de", "en", "nl", or
    the special string "porter" to get Porter's classic stemming algorithm for
    English.

    See also
    --------
    morphy: smarter approach to stemming (lemmatization), but only for English.
    """
    from Stemmer import Stemmer
    tokens = pipe(doc, fetch, _tokenize_if_needed)
    return Stemmer(language).stemWords(tokens)


@app.task
def stanford_ner_tag(doc, output="tokens"):
    """Named entity recognizer using Stanford NER.

    English-language name detection and classification.

    Currently only supports the model 'english.all.3class.distsim.crf.ser.gz'.

    Parameters
    ----------
    doc : document
        Either a single string or a handle on a document in the ES store.
        Tokenization and sentence splitting will be done by Stanford NER using
        its own rules.

    output : string, optional
        Output format. "tokens" gives a list of (token, nerclass) pairs,
        similar to the IO format but without the "I-". "names" returns a list
        of (name, class) pairs; since Stanford NER does not distinguish between
        start and continuation of name spans, the reconstruction of full names
        is heuristic.

    Returns
    -------
    tagged : list of list of pair of string
        For each sentence, a list of (word, tag) pairs.

    See also
    --------
    nlner_conll: NER tagger for Dutch.
    """
    from ._stanford_ner import tag
    return tag(fetch(doc), output)


@app.task
def pos_tag(tokens, model='nltk'):
    """Perform part-of-speech (POS) tagging for English.

    Currently only does English using the default model in NLTK.

    Expects a list of tokens.
    """
    if model != 'nltk':
        raise ValueError("unknown POS tagger %r" % model)
    nltk_download('averaged_perceptron_tagger')
    return nltk.pos_tag(tokens)


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


    See also
    --------
    movie_review_emotions: per-sentence fine-grained sentiment tagger

    movie_review_polarity: figure out if a movie review is positive or negative
    """
    from ._sentiwords import tag

    tagged = pipe(doc, fetch, _tokenize_if_needed, tag)
    if output == "bag":
        counts = {}
        for ngram, polarity in tagged:
            if polarity == 0:
                continue
            if ngram in counts:
                counts[ngram][1] += 1
            else:
                counts[ngram] = [polarity, 1]
        return counts

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
    nltk_download('punkt')
    return pipe(doc, fetch, nltk.word_tokenize)


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

    if not lang.isalpha():
        raise ValueError("not a valid language: %r" % lang)
    text = fetch(doc)
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
    """Wrapper around the Frog lemmatizer/POS tagger/NER/dependency parser.

    Expects Frog to be running in server mode, listening on
    ``localhost:${XTAS_FROG_PORT}`` or port 9987 if the environment variable
    ``XTAS_FROG_PORT`` is not set. It is *not* started for you.

    Currently, the module is only tested with all frog modules active except
    for the NER and parser.

    The following line starts Frog in the correct way:

    ``frog -S ${XTAS_FROG_PORT:-9887}``

    Parameters
    ----------
    output : string
        If 'raw', returns the raw output lines from Frog itself.
        If 'tokens', returns dictionaries for the tokens.
        If 'saf', returns a SAF dictionary.

    References
    ----------
    `Frog homepage <http://ilk.uvt.nl/frog/>`_

    See also
    --------
    nlner_conll: simple NER tagger for Dutch.
    """
    from ._frog import call_frog, parse_frog, frog_to_saf
    if output not in ('raw', 'tokens', 'saf'):
        raise ValueError("Unknown output: {output}, "
                         "please choose either raw, tokens, or saf"
                         .format(**locals()))
    result = pipe(doc, fetch, call_frog)
    if output == 'raw':
        return list(result)
    if output in ('tokens', 'saf'):
        result = parse_frog(result)
        if output == 'tokens':
            return list(result)
        return frog_to_saf(result)


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

    if lang not in endpoints_by_language and not api_url:
        raise ValueError("Not a valid language code: %r" % lang)

    if api_url is None:
        api_url = endpoints_by_language[lang]

    api_url += "/candidates"

    try:
        spotlight_resp = spotlight.candidates(
            api_url, text,
            confidence=conf,
            support=supp,
            spotter='Default'
        )
    except (spotlight.SpotlightException, TypeError) as e:
        return {'error': e.message}

    # Return a list of annotation dictionaries
    annotations = []
    for annotation in spotlight_resp:
        # Ignore annotations without disambiguation candidates
        if u'resource' in annotation:
            # Always return a list of resources, also for single candidates
            if isinstance(annotation[u'resource'], dict):
                annotation[u'resource'] = [annotation[u'resource']]
            annotations.append(annotation)

    return annotations


@app.task
def alpino(doc, output="raw"):
    """Wrapper around the Alpino (dependency) parser for Dutch.

    Expects an environment variable ALPINO_HOME to point at
    the Alpino installation dir.

    The script uses the 'dependencies' end_hook to generate lemmata and
    the dependency structure.

    Parameters
    ----------
    output : string
        If 'raw', returns the raw output from Alpino itself.
        If 'saf', returns a SAF dictionary.

    References
    ----------
    `Alpino homepage <http://www.let.rug.nl/vannoord/alp/Alpino/>`_.
    """
    from ._alpino import tokenize, parse_raw, interpret_parse

    try:
        transf = {"raw": identity, "saf": interpret_parse}[output]
    except KeyError:
        raise ValueError("Unknown output format %r" % output)

    return pipe(doc, fetch, tokenize, parse_raw, transf)


@app.task
def corenlp(doc, output='raw'):
    """Wrapper around the Stanford CoreNLP parser.

    CoreNLP is downloaded automatically.

    If run with all annotators, it requires around 3G of memory,
    and it will keep the process in memory indefinitely.

    Parameters
    ----------
    output : string
        If 'raw', returns the raw output lines from CoreNLP.
        If 'saf', returns a SAF dictionary.
    """
    from ._corenlp import parse, stanford_to_saf

    try:
        transf = {"raw": identity, "saf": stanford_to_saf}[output]
    except KeyError:
        raise ValueError("Unknown output format %r" % output)

    return pipe(doc, fetch, parse, transf)


@app.task
def corenlp_lemmatize(doc, output='raw'):
    """Wrapper around the Stanford CoreNLP lemmatizer.

    CoreNLP is downloaded automatically.

    Parameters
    ----------
    output : string
        If 'raw', returns the raw output lines from CoreNLP.
        If 'saf', returns a SAF dictionary.
    """
    from ._corenlp import parse, stanford_to_saf

    try:
        transf = {"raw": identity, "saf": stanford_to_saf}[output]
    except KeyError:
        raise ValueError("Unknown output format %r" % output)

    return pipe(doc, fetch, parse, transf)


@app.task
def semafor(saf):
    """Wrapper around the Semafor semantic parser.

    Expects semafor running in server mode listening to
    ``${SEMAFOR_HOST}:${SEMAFOR_PORT}`` (defaults to localhost:9888).
    It also expects ``$CORENLP_HOME`` to point to the CoreNLP installation dir.

    Input is expected to be a 'SAF' dictionary with trees and tokens.
    Output is a SAF dictionary with a frames attribute added.

    References
    ----------
    * `Semafor GitHub page <https://github.com/sammthomson/semafor>'_.
    * `CoreNLP home page <http://nlp.stanford.edu/software/corenlp.shtml>'_.
    """
    from ._semafor import add_frames
    add_frames(saf)
    return saf

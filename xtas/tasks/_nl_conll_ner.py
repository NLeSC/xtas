# Baseline NER tagger for Dutch based on the CoNLL dataset.
# Contributed by Daan Odijk (UvA), based on an example in the seqlearn
# package (https://github.com/larsmans/seqlearn).

from seqlearn.datasets import load_conll
from seqlearn.perceptron import StructuredPerceptron
from sklearn.feature_extraction import FeatureHasher

from six.moves.urllib.request import urlopen


_BASE_URL = 'http://www.cnts.ua.ac.be/conll2002/ner/data/ned.'


def _download_training_data():
    """Downloads CoNLL data (train + test).

    Returns an iterable over the lines of the concatenated dataset.
    """
    return (ln for part in "train testa testb".split()
               for ln in urlopen(_BASE_URL + part))


def _features(sentence, i):
    """Baseline named-entity recognition features for i'th token in sentence.
    """
    word = sentence[i].split()[0]

    yield "word:{}" + word.lower()

    if word[0].isupper():
        yield "CAP"

    if i > 0:
        yield "word-1:{}" + sentence[i - 1].lower()
        if i > 1:
            yield "word-2:{}" + sentence[i - 2].lower()
    if i + 1 < len(sentence):
        yield "word+1:{}" + sentence[i + 1].lower()
        if i + 2 < len(sentence):
            yield "word+2:{}" + sentence[i + 2].lower()


def _train_ner_model():
    X_train, y_train, lengths_train = load_conll(_download_training_data(),
                                                 _features)

    clf = StructuredPerceptron()
    clf.fit(X_train, y_train, lengths_train)
    return clf


_model = _train_ner_model()


def ner(tokens):
    """Baseline NER tagger for Dutch, based on the CoNLL'02 dataset."""

    global _model

    X = [_features(tokens, i) for i in range(len(tokens))]
    hasher = FeatureHasher(2**16, input_type="string")
    return zip(tokens, _model.predict(hasher.transform(X)))

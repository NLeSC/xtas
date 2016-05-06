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

# Baseline NER tagger for Dutch based on the CoNLL dataset.
# Contributed by Daan Odijk (UvA), based on an example in the seqlearn
# package (https://github.com/larsmans/seqlearn).

from urllib2 import urlopen

from seqlearn.datasets import load_conll
from seqlearn.perceptron import StructuredPerceptron
from sklearn.feature_extraction import FeatureHasher


_BASE_URL = 'http://www.cnts.ua.ac.be/conll2002/ner/data/ned.'


def _download_training_data():
    """Downloads CoNLL data (train + test).

    Returns an iterable over the lines of the concatenated dataset.
    """
    return (ln for part in ["train", "testa", "testb"]
               for ln in urlopen(_BASE_URL + part))


def _load_test_data():
    """Loads included test data, so people outside the CoNLL'02 project
    can test without violating the license.
    """
    import os
    selfdir = os.path.dirname(os.path.abspath(__file__))
    return open(os.path.join(selfdir, "conll_test_set.txt"))


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
    import sys
    if 'nose' in sys.modules:
        x_train, y_train, lengths_train = load_conll(_load_test_data(),
                                                 _features)
    else:
        x_train, y_train, lengths_train = load_conll(
                                                 _download_training_data(),
                                                 _features)

    clf = StructuredPerceptron()
    clf.fit(x_train, y_train, lengths_train)
    return clf


_model = _train_ner_model()


def ner(tokens):
    """Baseline NER tagger for Dutch, based on the CoNLL'02 dataset."""

    global _model

    X = [_features(tokens, i) for i in range(len(tokens))]
    hasher = FeatureHasher(2**16, input_type="string")
    return zip(tokens, _model.predict(hasher.transform(X)))

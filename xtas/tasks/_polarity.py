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

import errno
import os.path
from pprint import pprint
import tarfile
from tempfile import NamedTemporaryFile
from urllib import urlretrieve

from sklearn.datasets import load_files
from sklearn.externals.joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.grid_search import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from .._downloader import make_data_home, progress


_MODEL = None


_TRAINING_DATA = (
    'http://www.cs.cornell.edu/people/pabo/movie-review-data'
    '/review_polarity.tar.gz'
)


def _download():
    # TODO figure out the license on this one, maybe make the user perform
    # some action.
    data_dir = os.path.join(make_data_home(), 'movie_reviews')
    training_dir = os.path.join(data_dir, 'txt_sentoken')

    if not os.path.exists(training_dir):
        with NamedTemporaryFile() as temp:
            print("Downloading %r" % _TRAINING_DATA)
            urlretrieve(_TRAINING_DATA, temp.name, reporthook=progress)
            with tarfile.open(temp.name) as tar:
                tar.extractall(path=data_dir)

    return training_dir


def _train(param_search=False):
    data = load_files(_download())
    y = [data.target_names[t] for t in data.target]

    # The random state on the LR estimator is fixed to the most arbitrary value
    # that I could come up with. It is biased toward the middle number keys on
    # my keyboard.
    clf = make_pipeline(TfidfVectorizer(min_df=2, dtype=float,
                                        sublinear_tf=True,
                                        ngram_range=(1, 2),
                                        strip_accents='unicode'),
                        LogisticRegression(random_state=623, C=5000))

    if param_search:
        params = {'tfidf__ngram_range': [(1, 1), (1, 2)],
                  'lr__C': [1000, 5000, 10000]}

        print("Starting parameter search for review sentiment classification")
        # We ignore the original folds in the data, preferring a simple 5-fold
        # CV instead; this is intended to get a working model, not results for
        # publication.
        gs = GridSearchCV(clf, params, cv=5, refit=True, n_jobs=-1, verbose=2)
        gs.fit(data.data, y)

        print("Parameters found:")
        pprint(gs.best_params_)
        print("Cross-validation accuracy: %.3f" % gs.best_score_)

        return gs.best_estimator_

    else:
        print("Training logistic regression for movie review polarity")
        return clf.fit(data.data, y)


def classify(doc):
    global _MODEL
    if _MODEL is None:
        model_path = os.path.join(make_data_home("movie_reviews"),
                                  "classifier")
        try:
            _MODEL = load(model_path)
        except (IOError, OSError) as e:
            if e.errno == errno.ENOENT:
                _MODEL = _train()
                dump(_MODEL, model_path, compress=9)
            else:
                raise

    return _MODEL.predict_proba(doc)[0, 1]   # first sample, second class

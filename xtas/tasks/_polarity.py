import errno
import os.path
from pprint import pprint
import tarfile
from tempfile import NamedTemporaryFile

from six.moves.urllib.request import urlretrieve

from sklearn.datasets import load_files
from sklearn.externals.joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.grid_search import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from .._downloader import _make_data_home, _progress


MODEL = None


TRAINING_DATA = (
    'http://www.cs.cornell.edu/people/pabo/movie-review-data'
    '/review_polarity.tar.gz'
)


def download():
    # TODO figure out the license on this one, maybe make the user perform
    # some action.
    data_dir = os.path.join(_make_data_home(), 'movie_reviews')
    training_dir = os.path.join(data_dir, 'txt_sentoken')

    if not os.path.exists(training_dir):
        with NamedTemporaryFile() as temp:
            print("Downloading %r" % TRAINING_DATA)
            urlretrieve(TRAINING_DATA, temp.name, reporthook=_progress)
            with tarfile.open(temp.name) as tar:
                tar.extractall(path=data_dir)

    return training_dir


def train(param_search=False):
    data = load_files(download())
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
    global MODEL
    if MODEL is None:
        model_path = os.path.join(_make_data_home("movie_reviews"),
                                  "classifier")
        try:
            MODEL = load(model_path)
        except (IOError, OSError) as e:
            if e.errno == errno.ENOENT:
                MODEL = train()
                dump(MODEL, model_path, compress=9)
            else:
                raise

    return MODEL.predict_proba(doc)[0, 1]   # first sample, second class

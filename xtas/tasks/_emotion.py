from __future__ import print_function

from itertools import chain
import os.path
from shutil import copyfileobj, move
from tempfile import NamedTemporaryFile

from six.moves.urllib.request import urlopen

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.grid_search import GridSearchCV
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC

from .._downloader import _make_data_home


__all__ = ['classify']


_BASE_URL = "https://raw.githubusercontent.com/NLeSC/spudisc-emotion-classification/master/"


def download():
    data_home = _make_data_home() + os.path.sep
    path = os.path.join(data_home, "movie_review_emotions.txt")
    if not os.path.exists(path):
        tmp = NamedTemporaryFile(prefix=data_home, delete=False)
        try:
            for part in ["train.txt", "test.txt"]:
                copyfileobj(urlopen(_BASE_URL + part), tmp)
        except:
            tmp.close()
            os.remove(tmp)
            raise
        tmp.close()
        move(tmp.name, path)
    return path


class GridSearch(GridSearchCV):
    """Wrapper around GridSearchCV; workaround for scikit-learn issue #3484."""

    def decision_function(self, X):
        return super(GridSearch, self).decision_function(X)

    def predict(self, X):
        return super(GridSearch, self).predict(X)


data_train = [ln.rsplit(None, 1) for ln in open(download())]
X_train, Y_train = zip(*data_train)
del data_train

mlb = MultiLabelBinarizer()
Y_train = [set(s.split('_')) - {'None'} for s in Y_train]
Y_train = mlb.fit_transform(Y_train)


def train_grid_search():
    clf = make_pipeline(TfidfVectorizer(sublinear_tf=True, use_idf=False),
                        LinearSVC(dual=False))
    # XXX class_weight="auto" causes a lot of deprecation warnings, but it
    # still fares better than the new class_weight="balanced" heuristic.
    # n_jobs=-1 causes nosetests to hang so that is disabled for now.
    params = {'tfidfvectorizer__use_idf': [True, False],
              'tfidfvectorizer__sublinear_tf': [True, False],
              'linearsvc__class_weight': ["auto", None],
              'linearsvc__C': [.01, .1, 1, 10, 100, 1000],
              'linearsvc__penalty': ['l1', 'l2'],
              }
    clf = OneVsRestClassifier(GridSearch(clf, params, scoring='f1',
                                         verbose=1, cv=5))
    return clf.fit(X_train, Y_train)


clf = train_grid_search()
del X_train, Y_train


def classify(sentences):
    y = clf.predict(sentences)
    return mlb.inverse_transform(y)

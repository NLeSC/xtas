def train_movie_review_polarity(param_search=False):
    from .._downloader import download_movie_reviews, _make_data_home
    from pprint import pprint
    from sklearn.datasets import load_files
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.grid_search import GridSearchCV
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    data = load_files(download_movie_reviews())
    y = [data.target_names[t] for t in data.target]

    # The random state on the LR estimator is fixed to the most arbitrary value
    # that I could come up with. It is biased toward the middle number keys on
    # my keyboard.
    clf = Pipeline([('tfidf', TfidfVectorizer(min_df=2, dtype=float,
                                              sublinear_tf=True,
                                              ngram_range=(1, 2),
                                              strip_accents='unicode')),
                    ('lr', LogisticRegression(random_state=623, C=5000))])

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

#!/usr/bin/env python

# Copyright 2011-2013 University of Amsterdam
# Author: Lars Buitinck

from collections import defaultdict
from heapq import nlargest
import logging
import numpy as np

from .logsum import logsum


logger = logging.getLogger(__name__)


class ParsimoniousLM(object):
    """Language model for a set of documents.

    Constructing an object of this class fits a background model. The top
    method can then be used to fit document-specific models, also for unseen
    documents (with the same vocabulary as the background corpus).

    Parameters
    ----------
    documents : iterable over iterable over terms
    w : float
        Weight of document model (1 - weight of corpus model)
    thresh : int
        Don't include words that occur < thresh times

    Attributes
    ----------
    vocab : dict of term -> int
        Mapping of terms to numeric indices
    p_corpus : array of float
        Log prob of terms
    """

    def __init__(self, documents, w, thresh=0):
        logger.info('Building corpus model')

        self.w = w
        self.vocab = vocab = {}     # Vocabulary: maps terms to numeric indices
        count = defaultdict(int)    # Corpus frequency

        for d in documents:
            for tok in d:
                i = vocab.setdefault(tok, len(vocab))
                count[i] += 1

        cf = np.empty(len(count), dtype=np.float)
        for i, f in count.iteritems():
            cf[i] = f
        rare = (cf < thresh)
        cf -= rare * cf

        try:
            old_error_settings = np.seterr(divide='ignore')

            # lg P(t|C)
            self.p_corpus = np.log(cf) - np.log(np.sum(cf))
        finally:
            np.seterr(**old_error_settings)

    def top(self, k, d, max_iter=50, eps=1e-5, w=None):
        '''Get the top k terms of a document d and their log probabilities.

        Uses the Expectation Maximization (EM) algorithm to estimate term
        probabilities.

        Parameters
        ----------
        max_iter : int, optional
            Maximum number of iterations of EM algorithm to run.
        eps : float, optional
            Convergence threshold for EM algorithm.
        w : float, optional
            Weight of document model; overrides value given to __init__

        Returns
        -------
        t_p : list of (str, float)
        '''

        tf, p_term = self._document_model(d)
        p_term = self._EM(tf, p_term, w, max_iter, eps)

        terms = [(t, p_term[i]) for t, i in self.vocab.iteritems()]
        return nlargest(k, terms, lambda tp: tp[1])

    def _document_model(self, d):
        '''Build document model.

        Parameters
        ----------
        d : array of terms

        Returns
        -------
        tf : array of int
            Term frequencies
        p_term : array of float
            Term log probabilities

        Initial p_term is 1/n_distinct for terms with non-zero tf,
        0 for terms with 0 tf.
        '''

        logger.info('Gathering term probabilities')

        tf = np.zeros(len(self.vocab), dtype=np.float)  # Term frequency

        for tok in d:
            tf[self.vocab[tok]] += 1

        n_distinct = (tf > 0).sum()

        try:
            old_error_settings = np.seterr(divide='ignore')
            p_term = np.log(tf > 0) - np.log(n_distinct)
        finally:
            np.seterr(**old_error_settings)

        return tf, p_term

    def _EM(self, tf, p_term, w, max_iter, eps):
        '''Expectation maximization.

        Parameters
        ----------
        tf : array of float
            Term frequencies, as returned by document_model
        p_term : array of float
            Term probabilities, as returned by document_model
        max_iter : int
            Number of iterations to run.

        Returns
        -------
        p_term : array of float
            A posteriori term probabilities.
        '''

        logger.info('EM with max_iter=%d, eps=%g' % (max_iter, eps))

        if w is None:
            w = self.w
        w_ = np.log(1 - w)
        w = np.log(w)

        p_corpus = self.p_corpus + w_
        tf = np.log(tf)

        try:
            old_error_settings = np.seterr(divide='ignore')
            p_term = np.asarray(p_term)
            for i in xrange(1, max_iter + 1):
                # E-step
                p_term += w
                E = tf + p_term - np.logaddexp(p_corpus, p_term)

                # M-step
                new_p_term = E - logsum(E)

                diff = new_p_term - p_term
                p_term = new_p_term
                if (diff < eps).all():
                    logger.info('EM: convergence reached after %d iterations'
                                % i)
                    break
        finally:
            np.seterr(**old_error_settings)

        return p_term

#!/usr/bin/env python

from distutils.core import setup
import os.path


# Get __version__ from xtas source
dist_dir = os.path.dirname(os.path.abspath(__file__))
execfile(os.path.join(dist_dir, 'xtas/_version.py'))


def readme():
    with open(os.path.join(dist_dir, 'README.rst')) as f:
        return f.read()


setup(
    name="xtas",
    description="Distributed text analysis suite",
    long_description=readme(),
    author="Lars Buitinck",
    author_email="l.buitinck@esciencecenter.nl",
    packages=["xtas", "xtas.tasks", "xtas.webserver"],
    version=__version__,
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing",
    ],
    install_requires=[
        "celery>=3.0.0",
        "flask>=0.10.1",
        "nltk",
        "elasticsearch",
    ],
    extras_requires={
        "clustering": "scikit-learn>=0.13",
        "fast": "librabbitmq",
        "lda": "gensim",
        "wordclouds": "weighwords",
    },
)

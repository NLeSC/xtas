#!/usr/bin/env python

from distutils.core import setup

setup(
    name="xtas",
    description="Distributed text analysis suite",
    author="Lars Buitinck",
    author_email="l.buitinck@esciencecenter.nl",
    packages=["xtas", "xtas.webserver"],
    package_data={"xtas": ["templates/*.html"],
                  "xtas.configure": ["*.yaml"]},
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
        #"langid>=1.1.4dev",
        #"librabbitmq",
        "nltk",
        "rawes",
        "scikit-learn>=0.13",
        #"simplejson>=2.6.2",
    ],
)

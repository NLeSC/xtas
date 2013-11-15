#!/usr/bin/env python

from distutils.core import setup

setup(
    name="xtas",
    description="Distributed text analysis suite",
    author="Lars Buitinck",
    author_email="l.buitinck@esciencecenter.nl",
    packages=["xtas", "xtas.configure", "xtas.server", "xtas.tasks",
              "xtas.worker"],
    package_data={"xtas": ["templates/*.html"],
                  "xtas.configure": ["*.yaml"]},
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing",
    ],
    install_requires=[
        "celery>=3.0.0",
        "elasticsearch",
        "flask>=0.10.1",
        "langid",
        "nltk",
        "pyyaml>=3.10",
        "requests>=1.1.0",
        "simplejson>=2.6.2",
    ],
)

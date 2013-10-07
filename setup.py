#!/usr/bin/env python

from distutils.core import setup

setup(
    name="xtas",
    description="Distributed text analysis suite",
    author="Lars Buitinck",
    author_email="l.buitinck@esciencecenter.nl",
    packages=["xtas", "xtas.tasks"],
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing",
    ],
    install_requires=[
        "celery>=3.0.0",
        "flask>=0.10.1",
    ],
)

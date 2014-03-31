#!/usr/bin/env python

from distutils.core import setup
import os.path


# Get __version__ from xtas source
dist_dir = os.path.dirname(os.path.abspath(__file__))
execfile(os.path.join(dist_dir, 'xtas/_version.py'))


def readme():
    try:
        with open(os.path.join(dist_dir, 'README.rst')) as f:
            return f.read()
    except IOError:
        return ""


def requirements():
    with open(os.path.join(dist_dir, "requirements.txt")) as f:
        return f.readlines()


setup(
    name="xtas",
    description="Distributed text analysis suite",
    long_description=readme(),
    author="Lars Buitinck",
    author_email="l.buitinck@esciencecenter.nl",
    packages=["xtas", "xtas.tasks", "xtas.webserver"],
    package_data={"xtas.tasks": ["*.txt"]},
    url="https://github.com/NLeSC/xtas",
    version=__version__,
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing",
    ],
    install_requires=requirements(),
)

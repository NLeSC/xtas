#!/usr/bin/env python

from distutils.core import setup
import os.path
import sys


# Get __version__ from xtas source
dist_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(dist_dir, 'xtas/_version.py')) as versionpy:
    exec(versionpy.read())


def readme():
    try:
        with open(os.path.join(dist_dir, 'README.rst')) as f:
            return f.read()
    except IOError:
        return ""


def requirements():
    fname = "requirements%s.txt" % ("" if sys.version_info.major == 2 else "3")
    with open(os.path.join(dist_dir, fname)) as f:
        return f.readlines()


setup(
    name="xtas",
    description="Distributed text analysis suite",
    long_description=readme(),
    author="Lars Buitinck",
    author_email="l.buitinck@esciencecenter.nl",
    packages=["xtas", "xtas.make_config", "xtas.tasks", "xtas.tests",
              "xtas.webserver"],
    package_data={"xtas.tasks": ["*.txt", "NERServer.class"]},
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

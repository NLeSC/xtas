# Copyright 2013-2015 Netherlands eScience Center and University of Amsterdam
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python

import os.path

from setuptools import setup


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
    with open(os.path.join(dist_dir, "requirements.txt")) as f:
        return f.readlines()


setup(
    name="xtas",
    description="Distributed text analysis suite",
    long_description=readme(),
    author="Netherlands eScience Center",
    packages=["xtas", "xtas.tasks", "xtas.tests", "xtas.webserver"],
    package_data={"xtas.tasks": ["*.txt", "*.xml", "NERServer.class"]},
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

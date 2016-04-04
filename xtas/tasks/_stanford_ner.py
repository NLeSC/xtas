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

from __future__ import absolute_import, print_function
from itertools import groupby
import logging
import operator
import os
import os.path
from subprocess import Popen, PIPE

import nltk

from .._downloader import _download_zip


logger = logging.getLogger(__name__)


STANFORD_NER = (
    '''http://nlp.stanford.edu/software/stanford-ner-2014-01-04.zip'''
)


# Download and start server at import, not call time. Import is done lazily.
ner_dir = _download_zip(STANFORD_NER, name="Stanford NER",
                        check_dir="stanford-ner-2014-01-04")
jar = os.path.join(ner_dir, 'stanford-ner.jar')
model = os.path.join(ner_dir,
                     'classifiers/english.all.3class.distsim.crf.ser.gz')
classpath = '%s:%s' % (jar, os.path.dirname(__file__))
server = Popen(['java', '-mx1000m', '-cp', classpath, 'NERServer', model],
               stdin=PIPE, stdout=PIPE)


def tag(doc, format):
    """Implementation of tasks.single.stanford_ner_tag.

    Expects doc to be a string; for format and return value, see public API.
    """
    if format not in ["tokens", "names"]:
        raise ValueError("unknown format %r" % format)

    toks = nltk.word_tokenize(doc)
    text = u' '.join(toks).encode('utf-8')

    server.stdin.write(text)
    server.stdin.write('\n')

    tagged = [token.rsplit('/', 1)
              for token in server.stdout.readline().split()]

    if format == "tokens":
        return tagged
    elif format == "names":
        return [(' '.join(token for token, _ in tokens), cls)
                for cls, tokens in groupby(tagged, operator.itemgetter(1))
                if cls != 'O']

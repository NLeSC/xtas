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

# coding: utf-8

from nose.tools import assert_equal, assert_true

from xtas.tasks import stanford_ner_tag


def test_stanford_ner():
    # From Wikipedia front page, 10 Feb 2014.
    phrase = ("Academy Award-winning actor Philip Seymour Hoffman"
              " dies at the age of 46.")

    ne = stanford_ner_tag(phrase)
    for token, tag in ne:
        assert_true(isinstance(token, basestring))
        assert_true(tag in ["O", "PERSON"])

    names = stanford_ner_tag(phrase, output="names")
    # Stanford doesn't pick up "Academy Award". This is not our fault.
    # (XXX divise a better test.)
    assert_equal(names, [("Philip Seymour Hoffman", "PERSON")])


def test_stanford_ner_encoding():
    # Shouldn't raise an exception. Actually more a test for fetch/chardet,
    # but detected in the context of Stanford NER, so a non-regression test.
    stanford_ner_tag('\xe9toile'.decode('latin-1'))
    stanford_ner_tag('\xe9toile')

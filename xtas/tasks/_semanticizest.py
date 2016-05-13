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

import json
import os
import os.path
import urllib2


__all__ = ['Client']


class Client(object):
    """Client for running semanticizest REST server.

    Parameters
    ----------
    url : string
        Base URL of running semanticizest REST endpoint.
        See SemanticizerServer for a way to start a server from Python.

    Attributes
    ----------
    url : string
        URL of REST endpoint, as passed to the initializer.
    """

    def __init__(self, url):
        self.url = url

    def _call(self, method, text):
        """Call REST method."""
        url = os.path.join(self.url, method)
        req = urllib2.Request(url)
        response = urllib2.urlopen(req, json.dumps(text)).read()
        return json.loads(response)

    def all_candidates(self, sentence):
        ''' Given a sentence, generate a list of candidate entity links.

        Returns a list of candidate entity links, where each candidate entity
        is represented by a dictionary containing:
         - target     -- Title of the target link
         - offset     -- Offset of the anchor on the original sentence
         - length     -- Length of the anchor on the original sentence
         - commonness -- commonness of the link
         - senseprob  -- probability of the link
         - linkcount
         - ngramcount
        '''
        return self._call('all', sentence)

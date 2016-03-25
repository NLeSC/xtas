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

"""
Wrapper around the CoreNLP toolkit.
"""

import collections
from datetime import datetime
import io
import logging
import os
import os.path
import re
import subprocess
import threading
import time

from corenlp_xml.document import Document

from six import iteritems

from unidecode import unidecode

from .._downloader import _download_zip


log = logging.getLogger(__name__)

_CORENLP_VERSION = None


class StanfordCoreNLP(object):

    _singletons = {}  # annotators : object

    @classmethod
    def get_singleton(cls, annotators=None, **options):
        """
        Get or create a corenlp parser with the given annotator and options
        Note: multiple parsers with the same annotator and different options
              are not supported.
        """
        if annotators is not None:
            annotators = tuple(annotators)
        if annotators not in cls._singletons:
            cls._singletons[annotators] = cls(annotators, **options)
        return cls._singletons[annotators]

    def __init__(self, annotators=None, timeout=1000, memory="3G"):
        """
        Start the CoreNLP server with a system call.

        @param annotators: Which annotators to use, e.g.
                           ["tokenize", "ssplit", "pos", "lemma"]
        @param memory: Java heap memory to use
        """
        global _CORENLP_VERSION
        self.annotators = annotators
        self.memory = memory
        _CORENLP_VERSION = get_corenlp_version()
        self.start_corenlp()

    def start_corenlp(self):
        cmd = get_command(memory=self.memory, annotators=self.annotators)
        log.warn("Starting corenlp: {cmd}".format(**locals()))
        self.corenlp_process = subprocess.Popen(cmd, shell=True,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
        self.lock = threading.Lock()
        self.read_thread = threading.Thread(target=self.read_output_lines)
        self.read_thread.daemon = True
        self.read_thread.start()
        log.warn("Waiting for prompt")
        self.communicate(input=None, wait_for_output=False)

    def read_output_lines(self):
        "intended to be run as background thread to collect parser output"
        while True:
            chars = self.corenlp_process.stdout.readline()
            if chars == '':  # EOF
                break
            self.out.write(chars)

    def communicate(self, input, wait_for_output=True):
        log.warn("Sending {} bytes to corenlp".format(input and len(input)))
        if self.corenlp_process.poll() is not None:
            logging.warn("CoreNLP process died, respawning")
            self.start_corenlp()
        with self.lock:
            self.out = io.BytesIO()
            if input:
                self.corenlp_process.stdin.write(input)
                self.corenlp_process.stdin.write("\n\n")
                self.corenlp_process.stdin.flush()

            # wait until we get a prompt
            logging.warn("Waiting for NLP>")
            err_buffer = io.BytesIO()
            while True:
                char = self.corenlp_process.stderr.read(1)
                err_buffer.write(char)
                err_buffer.seek(-5, 2)
                if err_buffer.read() == "NLP> ":
                    break

        # give stdout a chance to flush
        # is there a better way to do this?
        while True:
            time.sleep(.1)
            result = self.out.getvalue()
            if result or not wait_for_output:
                return result

    def parse(self, text):
        """Call the server and return the raw results."""
        if isinstance(text, bytes):
            text = text.decode("ascii")
        text = re.sub("\s+", " ", unidecode(text))
        return self.communicate(text + "\n")


def parse(text, annotators=None, **options):
    s = StanfordCoreNLP.get_singleton(annotators, **options)
    return s.parse(text, **options)


# Stanford CoreNLP 3.4.1. Later versions require Java 8.
_URL = 'http://nlp.stanford.edu/software/stanford-corenlp-full-2014-08-27.zip'


def _get_corenlp():
    """Returns the directory where CoreNLP lives.

    Will download CoreNLP if necessary. Checks $CORENLP_HOME as well as
    $XTAS_DATA to be backward compatible.
    """
    corenlp_home = os.environ.get("CORENLP_HOME")
    return corenlp_home or _download_zip(_URL, name='Stanford CoreNLP')


def get_corenlp_version():
    "Return the corenlp version pointed at by CORENLP_HOME, or None"
    corenlp_home = _get_corenlp()
    for fn in os.listdir(corenlp_home):
        m = re.match("stanford-corenlp-([\d.]+)-models.jar", fn)
        if m:
            return m.group(1)


def get_command(annotators=None, memory=None):
    """Return the system (shell) call to run corenlp."""
    corenlp_home = _get_corenlp()
    cmd = 'java'
    if memory:
        cmd += ' -Xmx{memory}'.format(**locals())
    cmd += ' -cp "{}"'.format(os.path.join(corenlp_home, "*"))
    cmd += " edu.stanford.nlp.pipeline.StanfordCoreNLP -outputFormat xml"
    if annotators:
        cmd += ' -annotators {}'.format(",".join(annotators))
    return cmd


def stanford_to_saf(xml_bytes):
    doc = Document(xml_bytes)
    saf = collections.defaultdict(list)

    saf['header'] = {'format': "SAF",
                     'format-version': "0.0",
                     'processed':  {'module': "corenlp",
                                    'module-version': _CORENLP_VERSION,
                                    "started": datetime.now().isoformat()}
                     }
    tokens = {}     # (xml_sentid, xml_tokenid) : saf_tokenid

    def tokenid(sentid, tokenid):
        if (sentid, tokenid) in tokens:
            raise ValueError("Duplicate tokenid: {sentid}, {tokenid}"
                             .format(**locals()))
        saf_tokenid = len(tokens) + 1
        tokens[sentid, tokenid] = saf_tokenid
        return saf_tokenid

    for sent in doc.sentences:
        saf['tokens'] += [dict(id=tokenid(sent.id, t.id),
                               sentence=sent.id,
                               offset=t.character_offset_begin,
                               lemma=t.lemma, word=t.word,
                               pos=t.pos, pos1=POSMAP[t.pos])
                          for t in sent.tokens]

        saf['entities'] += [{'tokens': [tokens[sent.id, t.id]], 'type': t.ner}
                            for t in sent.tokens if t.ner not in (None, 'O')]

        if sent.collapsed_ccprocessed_dependencies:
            links = sent.collapsed_ccprocessed_dependencies.links
            saf['dependencies'] += [{'child': tokens[sent.id,
                                                     dep.dependent.idx],
                                     'parent': tokens[sent.id,
                                                      dep.governor.idx],
                                     'relation': dep.type}
                                    for dep in links if dep.type != 'root']

    if doc.coreferences:
        saf['coreferences'] = [[[tokens[m.sentence.id, t.id] for t in m.tokens]
                                for m in coref.mentions]
                               for coref in doc.coreferences]
    saf['trees'] = [{'sentence': s.id, 'tree': s.parse_string.strip()}
                    for s in doc.sentences if s.parse_string is not None]

    # remove default and empty elements
    return {k: v for (k, v) in iteritems(saf) if v != []}

POSMAP = {'CC': 'C',
          'CD': 'Q',
          'DT': 'D',
          'EX': '?',
          'FW': 'N',
          'IN': 'P',
          'JJ': 'A',
          'JJR': 'A',
          'JJS': 'A',
          'LS': 'C',
          'MD': 'V',
          'NN': 'N',
          'NNS': 'N',
          'NNP': 'M',
          'NNPS': 'M',
          'PDT': 'D',
          'POS': 'O',
          'PRP': 'O',
          'PRP$': 'O',
          'RB': 'B',
          'RBR': 'B',
          'RBS': 'B',
          'RP': 'R',
          'SYM': '.',
          'TO': '?',
          'UH': '!',
          'VB': 'V',
          'VBD': 'V',
          'VBG': 'V',
          'VBN': 'V',
          'VBP': 'V',
          'VBZ': 'V',
          'WDT': 'D',
          'WP': 'O',
          'WP$': 'O',
          'WRB': 'B',
          ',': '.',
          '.': '.',
          ':': '.',
          '``': '.',
          '$': '.',
          "''": '.',
          "#": '.',
          '-LRB-': '.',
          '-RRB-': '.',
          }

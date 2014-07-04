"""
Wrapper around the CoreNLP parser

The module expects CORENLP_HOME to point to the CoreNLP installation dir.

If run with all annotators, it requires around 3G of memory,
and it will keep the process in memory indefinitely.

See: http://nlp.stanford.edu/software/corenlp.shtml#Download

Tested with
http://nlp.stanford.edu/software/stanford-corenlp-full-2014-01-04.zip
"""


import datetime
from io import StringIO
import itertools
import logging
import os
import os.path
import re
import subprocess
import threading
import time

from six import iteritems

from unidecode import unidecode

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
        self.corenlp_process = subprocess.Popen(cmd, shell=True,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
        self.lock = threading.Lock()
        self.out_lines = []
        self.read_thread = threading.Thread(target=self.read_output_lines)
        self.read_thread.daemon = True
        self.read_thread.start()
        self.communicate(input=None)

    def read_output_lines(self):
        "intended to be run as background thread to collect parser output"
        while True:
            line = self.corenlp_process.stdout.readline()
            if line == '':  # EOF
                break
            self.out_lines.append(line.strip())

    def communicate(self, input):
        if self.corenlp_process.poll() is not None:
            logging.warn("CoreNLP process died, respawning")
            self.start_corenlp()
        with self.lock:
            self.out_lines = []

            if input:
                self.corenlp_process.stdin.write(input)
                self.corenlp_process.stdin.write("\n\n")
                self.corenlp_process.stdin.flush()

            # wait until we get a prompt
            err_buffer = StringIO()
            while True:
                err_buffer.write(self.corenlp_process.stderr.read(1))
                err_buffer.seek(-5, 2)
                if err_buffer.read() == "NLP> ":
                    break

        # give stdout a chance to flush
        # is there a better way to do this?
        time.sleep(.1)
        return self.out_lines

    def parse(self, text):
        """Call the server and return the raw results."""
        if isinstance(text, bytes):
            text = text.decode("ascii")
        text = re.sub("\s+", " ", unidecode(text))
        return self.communicate(text + "\n")


def parse(text, annotators=None, **options):
    s = StanfordCoreNLP.get_singleton(annotators, **options)
    return s.parse(text, **options)


def get_corenlp_version():
    "Return the corenlp version pointed at by CORENLP_HOME, or None"
    corenlp_home = os.environ.get("CORENLP_HOME")
    if corenlp_home:
        for fn in os.listdir(corenlp_home):
            m = re.match("stanford-corenlp-([\d.]+)-models.jar", fn)
            if m:
                return m.group(1)


def get_command(annotators=None, memory=None):
    "Return the system (shell) call to run corenlp"
    corenlp_home = os.environ.get("CORENLP_HOME")
    if not corenlp_home:
        raise Exception("CORENLP_HOME not set")
    cmd = 'java'
    if memory:
        cmd += ' -Xmx{memory}'.format(**locals())
    cmd += ' -cp "{}"'.format(os.path.join(corenlp_home, "*"))
    cmd += " edu.stanford.nlp.pipeline.StanfordCoreNLP"
    if annotators:
        cmd += ' -annotators {}'.format(",".join(annotators))
    return cmd


def stanford_to_saf(lines):
    """
    Convert stanfords 'interactive' text format to saf
    Unfortunately, stanford cannot return xml in interactive mode, so we
    need to parse their plain text format
    """
    processed = {'module': "corenlp",
                 'module-version': _CORENLP_VERSION,
                 "started": datetime.datetime.now().isoformat()}
    saf = {'header': {'format': "SAF",
                      'format-version': "0.0",
                      'processed': [processed]},
           'trees': [],
           'dependencies': [],
           'coreferences': [],
           'entities': []
           }
    tokens = {}  # sentence_no, index -> token

    def _regroups(pattern, text, **kargs):
        m = re.match(pattern, text, **kargs)
        if not m:
            raise Exception("Pattern {pattern!r} did not match text {text!r}"
                            .format(**locals()))
        return m.groups()

    while True:  # parse one sentence
        # skip leading blanks
        lines = itertools.dropwhile(lambda x: not x, lines)
        try:
            line = lines.next()
        except StopIteration:
            break  # done!
        if line == "Coreference set:":
            break  # skip to corefs
        sentence_no = int(_regroups("Sentence #\s*(\d+)\s+", line)[0])
        text = lines.next()

        log.debug("Parsing sentence {sentence_no}: {text!r}"
                  .format(**locals()))

        # Parse tokens
        for i, s in enumerate(re.findall('\[([^\]]+)\]', lines.next())):
            wd = dict(re.findall(r"([^=\s]*)=([^=\s]*)", s))
            tokenid = len(tokens) + 1
            token = dict(id=tokenid, word=wd['Text'], lemma=wd['Lemma'],
                         pos=wd['PartOfSpeech'], sentence=sentence_no,
                         offset=wd["CharacterOffsetBegin"])
            token['pos1'] = POSMAP[token['pos']]
            tokens[sentence_no, i] = token
            if wd.get('NamedEntityTag', 'O') != 'O':
                saf['entities'].append(dict(tokens=[tokenid],
                                            type=wd['NamedEntityTag']))
        # try to peek ahead to see if we have more than tokens
        lines, copy = itertools.tee(lines)
        try:
            peek = copy.next()
            if peek.startswith("Sentence #"):
                continue  # no tree/dependencies, skip to next sentence
        except StopIteration:
            break  # done!

        # Extract original tree
        tree = " ".join(itertools.takewhile(lambda x: x, lines))
        saf['trees'].append(dict(sentence=sentence_no, tree=tree))

        def parse_dependency(line):
            rfunc, parent, child = _regroups(RE_DEPENDENCY, line)
            if rfunc != 'root':
                parent, child = [tokens[sentence_no, int(j)-1]['id']
                                 for j in (parent, child)]
                saf['dependencies'].append(dict(child=child, parent=parent,
                                                relation=rfunc))
        # parse dependencies until blank line
        map(parse_dependency, itertools.takewhile(lambda x: x, lines))

    # get coreferences
    def get_coreference(lines):
        for line in itertools.takewhile(lambda l: l != "Coreference set:",
                                        lines):
            if line.strip():
                groups = _regroups(RE_COREF, line)
                yield [map(int, re.sub("[^\\d,]", "", s).split(","))
                       for s in groups]
    while True:
        corefs = list(get_coreference(lines))
        if not corefs:
            break
        for coref in corefs:
            sets = []
            for sent_index, head_index, from_index, to_index in coref:
                # take all nodes from .. to, place head first (False<True)
                indices = sorted(range(from_index, to_index),
                                 key=lambda i: (i != head_index, i))
                sets.append([tokens[sent_index, i-1]['id'] for i in indices])
            saf['coreferences'].append(sets)

    # add tokens and drop empty placeholders
    saf['tokens'] = tokens.values()
    return {k: v for (k, v) in iteritems(saf) if v}

RE_DEPENDENCY = "(\w+)\(.+-([0-9']+), .+-([0-9']+)\)"
RE_COREF = r'\s*\((\S+)\) -> \((\S+)\), that is: \".*\" -> \".*\"'
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

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
Wrapper around the RUG Alpino dependency parser.

The module expects ALPINO_HOME to point to the Alpino installation dir.
It was tested with the following version of Alpino:

http://www.let.rug.nl/vannoord/alp/Alpino/binary/binary/Alpino-x86_64-Linux-glibc-2.19-20908-sicstus.tar.gz

See: http://www.let.rug.nl/vannoord/alp/Alpino
"""


import datetime
import logging
import os
import re
import subprocess

log = logging.getLogger(__name__)

CMD_PARSE = ["bin/Alpino", "end_hook=dependencies", "-parse"]
CMD_TOKENIZE = ["Tokenization/tok"]


def parse_text(text):
    tokens = tokenize(text)
    parse = parse_raw(tokens)
    return interpret_parse(parse)


def tokenize(text):
    """
    Tokenize the given text using the alpino tokenizer.
    Input text should be a single unicode or utf-8 encoded string
    Returns a single utf-8 encoded string ready for Alpino,
    with spaces separating tokens and newlines sentences
    """
    alpino_home = os.environ['ALPINO_HOME']
    if isinstance(text, unicode):
        text = text.encode("utf-8")

    p = subprocess.Popen(CMD_TOKENIZE, shell=False, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=alpino_home)
    tokens, err = p.communicate(text)
    if 'error' in err or not tokens:
        raise Exception("Tokenization problem. Output was {tokens!r}, "
                        "error messages: {err!r}".format(**locals()))
    tokens = tokens.replace("|", "")  # alpino uses | for  'sid | line'
    return tokens


def parse_raw(tokens):
    alpino_home = os.environ['ALPINO_HOME']
    p = subprocess.Popen(CMD_PARSE, shell=False,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=alpino_home, env={'ALPINO_HOME': alpino_home})
    parse, err = p.communicate(tokens)
    if not parse:
        raise Exception("Parse problem. Output was {parse!r}, "
                        "error messages: {err!r}".format(**locals()))
    return parse


def interpret_parse(parse):
    module = {'module': "alpino",
              "started": datetime.datetime.now().isoformat()}
    header = {"header": {'format': "SAF",
                         'format-version': "0.0",
                         'processed': [module]
                         }}
    tokens = {}  # {(sid, offset): token}

    def get_token(sid, token_tuple):
        t = interpret_token(*token_tuple)
        if (sid, t['offset']) in tokens:
            return tokens[sid, t['offset']]
        else:
            tokens[sid, t['offset']] = t
            t['sentence'] = sid
            t['id'] = len(tokens)
            return t

    def get_deps(lines):
        for line in lines:
            # At some point, Alpino's dependencies end_hook started producing
            # "top" nodes, which we don't want in our output.
            if not line or line[0] == 'top':
                continue

            assert len(line) == 16
            sid = int(line[-1])
            parent = get_token(sid, line[:7])
            child = get_token(sid, line[8:15])
            func, rel = line[7].split("/")
            yield dict(child=child['id'], parent=parent['id'], relation=rel)

    lines = (line.decode("utf-8").strip().split("|")
             for line in parse.splitlines())
    dependencies = list(get_deps(lines))

    return dict(header=header, dependencies=dependencies,
                tokens=list(tokens.values()))



def interpret_token(lemma, word, begin, _end, major_pos, _pos2, pos):
    "Convert raw alpino token into a 'saf' dict"

    # Turn POS tags like "[stype=declarative]:verb" into just "verb" to
    # simulate the behavior of older Alpinos.
    pos = re.sub(r'^\[[^]]*\]:', '', pos)

    if pos == "denk_ik":  # is this a bug or a feature?
        major, minor = "verb", None
    elif "(" in pos:
        major, minor = pos.split("(", 1)
        minor = minor[:-1]
    else:
        major, minor = pos, None

    if "_" in major:
        m2 = major.split("_")[-1]
    else:
        m2 = major
    cat = _POSMAP.get(m2)
    if not cat:
        raise Exception("Unknown POS: %r (%s/%s/%s/%s)"
                        % (m2, major, begin, word, pos))

    return dict(word=word, lemma=lemma, pos=major_pos,
                offset=int(begin), pos_major=major,
                pos_minor=minor, pos1=cat)


_POSMAP = {"pronoun": 'O',
           "verb": 'V',
           "noun": 'N',
           "preposition": 'P',
           "determiner": "D",
           "comparative": "C",
           "adverb": "B",
           'adv': 'B',
           "adjective": "A",
           "complementizer": "C",
           "punct": ".",
           "conj": "C",
           "tag": "?",
           "particle": "R",
           "name": "M",
           "part": "R",
           "intensifier": "B",
           "number": "Q",
           "cat": "Q",
           "n": "Q",
           "reflexive":  'O',
           "conjunct": 'C',
           "pp": 'P',
           'anders': '?',
           'etc': '?',
           'enumeration': '?',
           'np': 'N',
           'p': 'P',
           'quant': 'Q',
           'sg': '?',
           'zo': '?',
           'max': '?',
           'mogelijk': '?',
           'sbar': '?',
           '--': '?',
           }

"""
Wrapper around the ILK Frog lemmatizer/POS tagger

See xtas.tasks.single.frog, http://ilk.uvt.nl/frog/.
"""

import datetime
import logging
import os
import socket

from unidecode import unidecode

FROG_HOST = "localhost"
FROG_PORT = os.environ.get('XTAS_FROG_PORT', 9887)
try:
    FROG_PORT = int(FROG_PORT)
except Exception as e:
    logging.warn("$FROG_PORT not recognized as port number, using %d: %r"
                 % (FROG_PORT, e))

_POSMAP = {"VZ": "P",
           "N": "N",
           "ADJ": "A",
           "LET": ".",
           "VNW": "O",
           "LID": "D",
           "SPEC": "M",
           "TW": "Q",
           "WW": "V",
           "BW": "B",
           "VG": "C",
           "TSW": "I",
           "MWU": "U",
           "": "?",
           }


def call_frog(text):
    """
    Call the frog parser on the given host and port with the given text
    Returns a file object containing the output lines.
    """
    if not text.endswith("\n"):
        text = text + "\n"
    if not isinstance(text, unicode):
        text = unicode(text)
    text = unidecode(text).encode("utf-8")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((FROG_HOST, FROG_PORT))
    s.sendall(text)
    s.shutdown(socket.SHUT_WR)
    for line in s.makefile('r'):
        line = line.strip('\n')
        if line == "READY":
            return
        else:
            yield line


def parse_frog(lines):
    """
    Interpret the output of the frog parser.
    Input should be a sequence of lines (i.e. the output of call_frog)
    Result is a sequence of dicts representing the tokens
    """
    sid = 0
    for i, l in enumerate(lines):
        if not l:
            # end of sentence marker
            sid += 1
        else:
            print(l.strip())
            parts = l.split("\t")
            tid, token, lemma, morph, pos, conf, ne, _, parent, rel = parts
            if rel:
                rel = (rel, int(parent) - 1)
            r = dict(id=i, sentence=sid, word=token, lemma=lemma,
                     pos=pos, pos_confidence=float(conf),
                     rel=rel)
            if ne != 'O':
                r["ne"] = ne.split('_', 1)[0][2:]   # NER label from BIO tags
            yield r


def add_pos1(token):
    """
    Adds a 'pos1' element to a frog token.
    """
    result = token.copy()
    result['pos1'] = _POSMAP[token['pos'].split("(")[0]]
    return result


def frog_to_saf(tokens):
    """
    Convert frog tokens into a new SAF document
    """
    tokens = [add_pos1(token) for token in tokens]
    module = {'module': "frog",
              "started": datetime.datetime.now().isoformat()}
    return {"header": {'format': "SAF",
                       'format-version': "0.0",
                       'processed': [module]
                       },
            "tokens": tokens}

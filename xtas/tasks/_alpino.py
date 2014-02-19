import subprocess
import logging
import os
import datetime

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
                         stdout=subprocess.PIPE, cwd=alpino_home)
    tokens, err = p.communicate(text)
    tokens = tokens.replace("|", "")  # alpino uses | for  'sid | line'
    return tokens


def parse_raw(tokens):
    alpino_home = os.environ['ALPINO_HOME']
    p = subprocess.Popen(CMD_PARSE, shell=False,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         cwd=alpino_home, env={'ALPINO_HOME': alpino_home})
    parse, err = p.communicate(tokens)
    return parse


def interpret_parse(parse):
    module = {'module': "alpino",
              "started": datetime.datetime.now().isoformat()}
    header = {"header": {'format': "SAF",
                         'format-version': "0.0",
                         'processed': [module]
                         }}
    tokens = {}  # {sid, offset: token}

    def get_token(sid, token_tuple):
        t = interpret_token(*token_tuple)
        print(t)
        if (sid, t['offset']) in tokens:
            return tokens[sid, t['offset']]
        else:
            tokens[sid, t['offset']] = t
            t['sentence'] = sid
            t['id'] = len(tokens)
            return t

    def get_dep(line):
        sid = int(line[-1])
        assert len(line) == 16
        parent = get_token(sid, line[:7])
        child = get_token(sid, line[8:15])
        func, rel = line[7].split("/")
        return dict(child=child['id'], parent=parent['id'], relation=rel)

    dependencies = [get_dep(line.strip().split("|"))
                    for line in parse.split("\n") if line.strip()]

    return dict(header=header, dependencies=dependencies,
                tokens=list(tokens.values()))


def interpret_token(lemma, word, begin, _end, major_pos, _pos2, pos):
    "Convert to raw alpino token into a 'saf' dict"
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
    cat = POSMAP.get(m2)
    if not cat:
        raise Exception("Unknown POS: %r (%s/%s/%s/%s)"
                        % (m2, major, begin, word, pos))

    return dict(word=word, lemma=lemma, pos=major_pos,
                offset=int(begin), pos_major=major,
                pos_minor=minor, pos1=cat)


POSMAP = {"pronoun": 'O',
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


if __name__ == '__main__':
    import sys
    import json
    p = parse_text(" ".join(sys.argv[1:]))
    print(json.dumps(p, indent=2))

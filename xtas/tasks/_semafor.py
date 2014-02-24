"""
Semafor semantic parser

This module requires the semafor web service running at
SEMAFOR_HOST:SEMAFOR_PORT (defaults to localhost:9888).

The to_conll and add_frames method also convert 'Penn' style
trees to conll format, which requires CORENLP_HOME to point
to a CoreNLP installation dir.

See: https://github.com/sammthomson/semafor
(and: http://nlp.stanford.edu/software/corenlp.shtml

Brief installation instructions for semafor
- Clone/download semafor
- Build with mvn package
- Download semafor malt model
- Run the web server:
java -Xms4g -Xmx4g -cp target/Semafor-3.0-alpha-04.jar \
    edu.cmu.cs.lti.ark.fn.SemaforSocketServer \
    model-dir:/path/to/semafor_malt_model_20121129 port:9888
"""

from __future__ import absolute_import

import datetime
import socket
import json
import os
import tempfile
import subprocess
from cStringIO import StringIO


def nc(host, port, input):
    """'netcat' implementation, see http://stackoverflow.com/a/1909355"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(input)
    s.shutdown(socket.SHUT_WR)
    s.settimeout(5)
    result = StringIO()
    while 1:
        data = s.recv(1024)
        if data == "":
            s.close()
            return result.getvalue()
        result.write(data)


def call_semafor(conll_str):
    """
    Use semafor to parse the conll_str.
    """
    host = os.environ.get("SEMAFOR_HOST", "localhost")
    port = int(os.environ.get("SEMAFOR_PORT", 9888))
    result = nc(host, port, conll_str)
    return [json.loads(sent) for sent in result.split("\n") if sent.strip()]


def to_conll(tree):
    """
    Convert a parse tree from Penn (?) to conll
    """
    classpath = os.path.join(os.environ["CORENLP_HOME"], "*")
    javaclass = "edu.stanford.nlp.trees.EnglishGrammaticalStructure"
    # create stub xml file and call the conll class
    xml = ("<root><document><sentences><sentence>{tree}"
           "</sentence></sentences></document></root>"
           .format(**locals()))
    with tempfile.NamedTemporaryFile() as f:
        f.write(xml)
        f.flush()
        cmd = ('java -cp "{classpath}" {javaclass} -conllx -treeFile {f.name}'
               .format(**locals()))
        return subprocess.check_output(cmd, shell=True)


def add_frames(saf_article):
    """
    Adds frames to a SAF-article, which should have a "trees" attribute
    with penn-style trees. The article will be modified in-place
    """
    saf_article['frames'] = []
    provenance = {'module': "semafor",
                  "started": datetime.datetime.now().isoformat()}
    saf_article['header']['processed'].append(provenance)

    for t in saf_article['trees']:
        sid = int(t['sentence'])
        tree = t['tree']
        conll = to_conll(tree)
        tokens = sorted((w for w in saf_article['tokens']
                         if w['sentence'] == sid),
                        key=lambda token: int(token['offset']))
        try:
            sent, = call_semafor(conll)
        except socket.timeout, e:
            err = {"module": module, "sentence": sid, "error": unicode(e)}
            saf_article.setdefault('errors', []).append(err)
            continue
        frames, sem_tokens = sent["frames"], sent["tokens"]
        assert len(tokens) == len(sem_tokens)

        def get_tokenids(f):
            for span in f["spans"]:
                for i in range(span["start"], span["end"]):
                    yield tokens[i]['id']

        for frame in frames:
            f = {"sentence": sid,
                 "name": frame["target"]["name"],
                 "target": list(get_tokenids(frame["target"])),
                 "elements": []}
            for a in frame["annotationSets"][0]["frameElements"]:
                f["elements"].append({"name": a["name"],
                                      "target": list(get_tokenids(a))})
            saf_article['frames'].append(f)

    return saf_article

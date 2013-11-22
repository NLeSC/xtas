from nltk import word_tokenize

from ..taskregistry import task
#from ..util import getconf


@task()
def tokenize(text, config):
    return word_tokenize(text)

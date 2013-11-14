import langid
import requests

from ..taskregistry import task
from ..util import getconf, slashjoin


@task('/langid/<index>/<doc_type>/<int:id>')
def guess(doc_type, id, index, config):
    es = getconf(config, 'main elasticsearch', error='raise')
    doc = requests.get(slashjoin([es, index, doc_type, str(id)]))
    content = doc.json()['_source']['body']

    return langid.rank(content)

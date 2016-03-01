from os.path import join
import subprocess
import tempfile
import xml.etree.ElementTree as etree

from .._downloader import _download_zip, _make_data_home


_zip = 'https://github.com/HeidelTime/heideltime/releases/download/VERSION2.1/heideltime-standalone-2.1.zip'

_heideltime_dir = _download_zip(url=_zip, name='Heideltime',
                                check_dir='heideltime-standalone')

# In config.props.xtas, set the path to the TreeTagger home dir.
_config_in = join(_heideltime_dir, 'config.props')
_config_props = join(_heideltime_dir, 'config.props.xtas')
with open(join(_heideltime_dir, 'config.props')) as config_in:
    with open(_config_props, 'w') as config_out:
        for line in config_in:
            if line.startswith('treeTaggerHome = SET ME'):
                treetagger_home = join(_make_data_home(), 'treetagger')
                line = 'treeTaggerHome = %s\n' % treetagger_home
            config_out.write(line)

_jar = join(_heideltime_dir, 'de.unihd.dbs.heideltime.standalone.jar')


def call_heideltime(doc, language):
    with tempfile.NamedTemporaryFile(prefix='xtas-heideltime') as f:
        f.write(doc.encode('utf-8') if isinstance(doc, unicode) else doc)
        f.flush()
        out = subprocess.check_output(['java', '-jar', _jar,
                                       '-c', _config_props,
                                       '-l', language, '-pos', 'treetagger',
                                       f.name])
    out = etree.fromstring(out.replace('&', '&amp;'))
    out = [x.attrib['value'] for x in out.findall('TIMEX3')]

    return out

from os.path import dirname, join
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as etree

from .._downloader import _download_zip, _make_data_home


_heideltime_dir = _download_zip(url='http://goo.gl/mx5ckK', name='Heideltime',
                                check_dir='heideltime-standalone')
_jar = join(_heideltime_dir, 'de.unihd.dbs.heideltime.standalone.jar')

_config_props = join(_heideltime_dir, 'config.props.xtas')

shutil.copyfile(join(_heideltime_dir, 'config.props'), _config_props)

# Ugliest hack evah
subprocess.call(['sed', '-i',
                 's|^treeTaggerHome .*|treeTaggerHome = %s|'
                    % (join(_make_data_home(), 'treetagger')),
                 _config_props])


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

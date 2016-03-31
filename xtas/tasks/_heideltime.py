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

import errno
import os
from os.path import join
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as etree

from .._downloader import _download_zip, _make_data_home


def _set_treetagger_home(heideltime_dir):
    """Point Heideltime to TreeTagger installation dir.

    Heideltime needs to know where TreeTagger lives (which we don't install
    automatically for licensing reasons). We therefore edit its configuration
    file, {heideltime_dir}/config.props, producing a new one at
    {heideltime_dir}/config.props.xtas.

    Returns the path of the new configuration file.
    """
    final_path = join(heideltime_dir, 'config.props.xtas')
    home = None

    try:
        in_path = join(heideltime_dir, 'config.props')
        with open(in_path) as config_in:
            config_out = tempfile.NamedTemporaryFile(dir=heideltime_dir,
                                                     delete=False)
            for line in config_in:
                if line.startswith('treeTaggerHome = SET ME'):
                    home = join(_make_data_home(), 'treetagger')
                    line = 'treeTaggerHome = %s\n' % home
                config_out.write(line)

        if home is None:
            raise Exception("didn't find treeTaggerHome in %r" % in_path)

        shutil.move(config_out.name, final_path)

    except:
        os.remove(config_out.name)
        raise

    return final_path


# None signals not initialized.
_config_props = None
_jar = None


def _initialize():
    # XXX We should synchronize across worker threads.
    global _config_props, _jar
    if _config_props is not None:
        return

    _zip = 'https://github.com/HeidelTime/heideltime/releases/download/VERSION2.1/heideltime-standalone-2.1.zip'

    _heideltime_dir = _download_zip(url=_zip, name='Heideltime',
                                    check_dir='heideltime-standalone')
    _config_props = _set_treetagger_home(_heideltime_dir)
    _jar = join(_heideltime_dir, 'de.unihd.dbs.heideltime.standalone.jar')


def call_heideltime(doc, language, output):
    """Implementation of tasks.heideltime; see there for documentation."""
    output = output.lower()
    if output not in ["timeml", "dicts", "values"]:
        raise ValueError("unknown output format %r" % output)

    with tempfile.NamedTemporaryFile(prefix='xtas-heideltime') as f:
        f.write(doc.encode('utf-8') if isinstance(doc, unicode) else doc)
        f.flush()
        out = subprocess.check_output(['java', '-jar', _jar,
                                       '-c', _config_props,
                                       '-l', language, '-pos', 'treetagger',
                                       f.name])

    # Heideltime doesn't always escape its ampersands correctly.
    out = out.replace('&', '&amp;')

    if output != "timeml":
        out = etree.fromstring(out).findall("TIMEX3")
        if output == "dicts":
            out = [dict(timex.items()) for timex in out]
        else:
            out = [timex.attrib['value'] for timex in out]

    return out

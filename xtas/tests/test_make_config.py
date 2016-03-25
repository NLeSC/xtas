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

from nose.tools import assert_in

from xtas.make_config import _get_default_config


def test_get_config():
    with _get_default_config() as default:
        compiled = compile(default.read(), 'xtas_config.py', mode='exec')
    for name in ['CELERY', 'ELASTICSEARCH', 'EXTRA_MODULES']:
        assert_in(name, compiled.co_names)

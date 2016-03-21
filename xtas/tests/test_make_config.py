from nose.tools import assert_in

from xtas.make_config import _get_default_config


def test_get_config():
    with _get_default_config() as default:
        compiled = compile(default.read(), 'xtas_config.py', mode='exec')
    for name in ['CELERY', 'ELASTICSEARCH', 'EXTRA_MODULES']:
        assert_in(name, compiled.co_names)

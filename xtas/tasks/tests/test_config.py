from nose.tools import assert_equal, assert_raises
from xtas.tasks import config


def test_config():
    """Test the config task."""

    cfg = {}
    assert_raises(ValueError, config, cfg)

    cfg = {'foo': {'bar': 'baz'}, 'main': {'debug': True}}
    assert_equal(cfg, config(cfg))

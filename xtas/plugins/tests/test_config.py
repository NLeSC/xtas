from nose.tools import assert_equal, assert_raises
from xtas.tasks import show_config


def test_config():
    """Test the config task."""

    cfg = {}
    assert_raises(ValueError, show_config, cfg)

    cfg = {'foo': {'bar': 'baz'}, 'main': {'debug': True}}
    assert_equal(cfg, config(cfg))

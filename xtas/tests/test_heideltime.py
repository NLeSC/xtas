import os
from os import path
from shutil import copyfile, rmtree
from tempfile import mkdtemp
import xml.etree.ElementTree as etree

from nose import SkipTest
from nose.tools import assert_equal, assert_false, assert_raises

from xtas.tasks import heideltime
from xtas.tasks._heideltime import _set_treetagger_home


def test_set_treetagger_home():
    config_props = path.join(path.dirname(__file__), 'config.props')
    directory = mkdtemp(prefix='xtas-heideltime-test.')
    try:
        temp = path.join(directory, 'config.props')
        copyfile(config_props, path.join(directory, 'config.props'))
        config_props_out = _set_treetagger_home(directory)

        assert_equal(config_props_out,
                     path.join(directory, 'config.props.xtas'))

        # Test exception handling on empty config.props.
        with open(temp, 'w'):
            pass    # Empty file.
        os.remove(config_props_out)

        assert_raises(Exception, _set_treetagger_home, directory)
        assert_false(path.exists(config_props_out))
    finally:
        rmtree(directory)
        pass


def test_heideltime():
    raise SkipTest("Heideltime needs TreeTagger installed")

    example = "Lunch at 12:00pm & New Year on January 1st."

    timeml = heideltime(example, output="timeml")
    noon, newyear = etree.fromstring(timeml).findall("TIMEX3")

    assert_equal("TIME", noon.attrib["type"])
    assert_equal("DATE", newyear.attrib["type"])

    value1, value2 = heideltime(example)
    assert_equal(value1, noon.attrib["value"])
    assert_equal(value2, newyear.attrib["value"])

    time, = heideltime("Twaalf uur lang.", language="dutch", output="dicts")
    assert_equal(list(time.keys()), ['tid', 'type', 'value'])
    assert_equal(time['type'], 'DURATION')
    assert_equal(time['value'], 'P12H')

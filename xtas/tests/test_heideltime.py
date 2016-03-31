import xml.etree.ElementTree as etree

from nose import SkipTest
from nose.tools import assert_equal

from xtas.tasks import heideltime


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

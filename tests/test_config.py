import os
from xml.etree.cElementTree import ParseError

import pytest

from msl.equipment.config import Config


def test_config_io_errors():

    # xml file does not exist
    with pytest.raises(IOError):
        Config('does_not_exist.xml')

    # invalid xml file
    with pytest.raises(ParseError):
        Config(os.path.join(os.path.dirname(__file__), 'config0.xml'))


def test_config_constants():

    # the default Config values
    assert Config.PyVISA_LIBRARY == '@ni'
    assert not Config.DEMO_MODE
    assert len(Config.PATH) == 0

    path = os.path.join(os.path.dirname(__file__), 'config1.xml')
    c = Config(path)

    # the new Config values
    assert path == c.path
    assert c.root.tag == 'msl'
    assert Config.PyVISA_LIBRARY == '@py'
    assert Config.DEMO_MODE
    assert len(Config.PATH) > 0
    assert 'docs' in Config.PATH
    assert os.path.join('docs', '_api') in Config.PATH
    assert os.path.join('docs', '_static') in os.environ['PATH']
    assert os.path.join('docs', '_templates') in os.environ['PATH']
    assert c.value('SOME_VALUE') == '1.2345'

    # database default values
    assert path == c.database().path
    assert c.database().equipment == {}
    assert c.database().records() == []
    assert c.database().connections() == []


def test_config_constants_reloaded():

    # make sure that loading a new config file does not alter the class-level attributes
    path = os.path.join(os.path.dirname(__file__), 'config2.xml')
    c = Config(path)

    assert path == c.path
    assert Config.PyVISA_LIBRARY == '@py'
    assert Config.DEMO_MODE
    assert 'docs' in Config.PATH

    assert len(c.database().records()) == 7

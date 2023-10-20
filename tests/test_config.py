from __future__ import annotations

import os
from io import BytesIO
from xml.etree.ElementTree import ParseError

import pytest

from msl.equipment.config import Config

ROOT_DIR = os.path.join(os.path.dirname(__file__), 'db_files')


def teardown_module():
    import cleanup_os_environ
    cleanup_os_environ.cleanup()


def test_config_io_errors():

    # xml file does not exist
    with pytest.raises(OSError):
        Config('does_not_exist.xml')

    # invalid xml file
    with pytest.raises(ParseError):
        Config(os.path.join(ROOT_DIR, 'config0.xml'))


def test_config_constants():

    # the default Config values
    assert Config.GPIB_LIBRARY == ''
    assert Config.PyVISA_LIBRARY == '@ivi'
    assert not Config.DEMO_MODE
    assert len(Config.PATH) == 0

    path = os.path.join(ROOT_DIR, 'config1.xml')
    c = Config(path)

    # the new Config values
    assert path == c.path
    assert c.root.tag == 'msl'
    assert Config.GPIB_LIBRARY == r'C:\gpib\ni4822.dll'
    assert Config.PyVISA_LIBRARY == '@py'
    assert Config.DEMO_MODE
    assert len(Config.PATH) > 0
    assert 'docs' in Config.PATH
    assert os.path.join('docs', '_api') in Config.PATH
    assert os.path.join('docs', '_static') in os.environ['PATH']
    assert os.path.join('docs', '_templates') in os.environ['PATH']
    assert c.value('some_value') == 1.2345
    assert c.value('gpib_library') == r'C:\gpib\ni4822.dll'
    assert c.value('pyvisa_library') == '@py'
    assert c.value('demo_mode') is True

    # database default values
    assert path == c.database().path
    assert c.database().equipment == {}
    assert c.database().records() == []
    assert c.database().connections() == []


def test_config_constants_reloaded():

    # make sure that loading a new config file does not alter the class-level attributes
    path = os.path.join(ROOT_DIR, 'config2.xml')
    c = Config(path)

    assert path == c.path
    assert Config.GPIB_LIBRARY == r'C:\gpib\ni4822.dll'
    assert Config.PyVISA_LIBRARY == '@py'
    assert Config.DEMO_MODE
    assert 'docs' in Config.PATH

    assert len(c.database().records()) == 7

    # reset the default Config values so that other tests can assume the default values
    Config.GPIB_LIBRARY = ''
    Config.PyVISA_LIBRARY = '@ivi'
    Config.DEMO_MODE = False
    assert Config.GPIB_LIBRARY == ''
    assert Config.PyVISA_LIBRARY == '@ivi'
    assert not Config.DEMO_MODE


def test_elements():
    contents = BytesIO(
        b"""<?xml version="1.0" encoding="utf-8" ?>
    <msl>
        <fruits>
          <fruit colour="red">apple</fruit>
          <fruit colour="orange">orange</fruit>
          <fruit colour="yellow">mango</fruit>
        </fruits>

        <numbers i1="0" i2="-987" f1="1.234" f2="-9.2e-6" c1="7j" c2="-1-0.7j"/>
        <cases n1="None" n2="none" b1="true" b2="TruE" b3="false" b4="FalSe"/>
        <strings s1="value" s2="[1,2, 3]"/>

        <veggie colour="orange">carrot</veggie>
        <veggie colour="red">beet</veggie>
        <veggie colour="green">asparagus</veggie>
        
        <n1>NONE</n1>
        <n2>none</n2>
        <b1>true</b1>
        <b2>False</b2>
        <i1>0</i1>
        <i2>-99999</i2>
        <f1>1.23</f1>
        <f2>-1.712e-12</f2>
        <c1>8.1j</c1>
        <c2>-7e4+8e2j</c2>

    </msl>"""
    )

    c = Config(contents)
    assert c.path == '<BytesIO>'

    assert c.root.tag == 'msl'
    assert c.root.text.strip() == ''

    assert c.value('invalid') is None
    assert c.value('invalid', 7) == 7
    assert c.find('invalid') is None
    assert c.findall('invalid') == []
    assert c.attrib('invalid') == {}

    assert c.value('fruits').strip() == ''
    assert c.find('fruits').text.strip() == ''
    assert len(c.findall('fruits')) == 1
    assert c.attrib('fruits') == {}

    assert c.value('fruit') is None
    assert c.value('fruit', False) is False
    assert c.find('fruit') is None
    assert c.findall('fruit') == []
    assert c.attrib('fruit') == {}

    assert c.value('fruits/fruit') == 'apple'
    assert c.value('fruits/veggie', 1.2) == 1.2
    assert c.find('fruits/fruit').text == 'apple'
    assert len(c.findall('fruits/fruit')) == 3
    assert c.attrib('fruits/fruit') == {'colour': 'red'}

    assert c.value('veggie') == 'carrot'
    assert c.find('veggie').text == 'carrot'
    assert len(c.findall('veggie')) == 3
    assert c.attrib('veggie') == {'colour': 'orange'}

    assert c.value('numbers') is None
    assert c.value('numbers', 0) is None
    assert c.find('numbers').text is None
    assert len(c.findall('numbers')) == 1
    assert c.attrib('numbers') == {
        'i1': 0, 'i2': -987, 'f1': 1.234,
        'f2': -9.2e-6, 'c1': 7j, 'c2': -1 - 0.7j}

    assert c.attrib('cases') == {
        'n1': None, 'n2': None, 'b1': True,
        'b2': True, 'b3': False, 'b4': False}

    assert c.attrib('strings') == {'s1': 'value', 's2': '[1,2, 3]'}

    assert c.value('n1') is None
    assert c.value('n1', 1) is None
    assert c.value('n2') is None
    assert c.value('n2', 1) is None
    assert c.value('n1') is None
    assert c.value('b1') is True
    assert c.value('b2') is False
    assert c.value('i1') == 0
    assert isinstance(c.value('i1'), int)
    assert c.value('i2') == -99999
    assert isinstance(c.value('i2'), int)
    assert c.value('f1') == 1.23
    assert c.value('f2') == -1.712e-12
    assert c.value('c1') == 8.1j
    assert c.value('c2') == -7e4 + 8e2j

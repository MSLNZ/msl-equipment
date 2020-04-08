import os

import pytest

from msl.equipment.config import Config

ROOT_DIR = os.path.join(os.path.dirname(__file__), 'db_files')


def teardown_module():
    import cleanup_os_environ
    cleanup_os_environ.cleanup()


def test_config_io_errors():

    # xml file does not exist
    with pytest.raises(IOError):
        Config('does_not_exist.xml')

    # invalid xml file
    with pytest.raises(IOError):
        Config(os.path.join(ROOT_DIR, 'config0.xml'))


def test_config_constants():

    # the default Config values
    assert Config.PyVISA_LIBRARY == '@ni'
    assert not Config.DEMO_MODE
    assert len(Config.PATH) == 0

    path = os.path.join(ROOT_DIR, 'config1.xml')
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
    assert c.value('some_value') == 1.2345
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
    assert Config.PyVISA_LIBRARY == '@py'
    assert Config.DEMO_MODE
    assert 'docs' in Config.PATH

    assert len(c.database().records()) == 7

    # reset the default Config values so that other tests can assume the default values
    Config.PyVISA_LIBRARY = '@ni'
    Config.DEMO_MODE = False
    assert Config.PyVISA_LIBRARY == '@ni'
    assert not Config.DEMO_MODE

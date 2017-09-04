import os
import sys

import pytest

from msl.equipment.config import Config
from msl.equipment.connection_msl import ConnectionMessageBased


def test_database_io_errors():

    # no <path></path> tag
    with pytest.raises(IOError) as err:
        Config(os.path.join(os.path.dirname(__file__), 'db_err0.xml')).database()
    assert '<path>' in str(err.value)

    # database file does not exist
    with pytest.raises(IOError):
        Config(os.path.join(os.path.dirname(__file__), 'db_err1.xml')).database()

    # unsupported database file
    with pytest.raises(IOError) as err:
        Config(os.path.join(os.path.dirname(__file__), 'db_err2.xml')).database()
    assert 'database' in str(err.value)

    # more than 1 Sheet in the Excel database
    with pytest.raises(IOError) as err:
        Config(os.path.join(os.path.dirname(__file__), 'db_err3.xml')).database()
    assert 'Sheet' in str(err.value)

    # the 'equipment' item in the xml file is not a valid Equipment Record
    with pytest.raises(AttributeError) as err:
        Config(os.path.join(os.path.dirname(__file__), 'db_err4.xml')).database()
    assert 'attributes' in str(err.value)

    # the 'equipment' item in the xml file is not a unique Equipment Record
    with pytest.raises(AttributeError) as err:
        Config(os.path.join(os.path.dirname(__file__), 'db_err5.xml')).database()
    assert 'unique' in str(err.value)

    # the 'equipment' item in the xml file is has multiple aliases
    with pytest.raises(ValueError) as err:
        Config(os.path.join(os.path.dirname(__file__), 'db_err6.xml')).database()
    assert 'aliases' in str(err.value)

    # invalid Sheet name in Excel database
    with pytest.raises(IOError) as err:
        Config(os.path.join(os.path.dirname(__file__), 'db_err7.xml')).database()
    assert 'Sheet' in str(err.value)


def test_database():

    path = os.path.join(os.path.dirname(__file__), 'db.xml')
    c = Config(path)

    dbase = c.database()
    assert path == dbase.path
    assert len(dbase.records()) == 7 + 18
    assert len(dbase.records(manufacturer='NOPE!')) == 0
    assert len(dbase.records(manufacturer='^Ag')) == 10  # all records from Agilent
    assert len(dbase.records(manufacturer='Agilent', model='83640L')) == 1
    assert len(dbase.records(manufacturer='H*P')) == 2  # all records from Hewlett Packard
    assert len(dbase.records(manufacturer='Bd6d850614')) == 1
    assert len(dbase.records(location='General')) == 3
    assert len(dbase.records(location='RF Lab')) == 9
    assert len(dbase.records(model='00000')) == 1

    assert len(dbase.connections()) == 10
    assert len(dbase.connections(backend='MSL')) == 5
    assert len(dbase.connections(serial='A10008')) == 1
    assert len(dbase.connections(manufacturer='^Ag')) == 4  # all records from Agilent
    assert len(dbase.connections(model='DTMc300V_sub')) == 1
    assert len(dbase.connections(manufacturer='Agilent', serial='G00001')) == 1

    assert len(dbase.equipment) == 2
    assert '712ae' in dbase.equipment  # the model number is used as the key
    assert 'dvm' in dbase.equipment  # the alias is used as the key


def test_connection_properties():

    dbase = Config(os.path.join(os.path.dirname(__file__), 'db.xml')).database()
    props = dbase.records(serial='37871232')[0].connection.properties

    assert props['a'] == 1
    assert props['b'] == 1.1
    assert isinstance(props['c'], bool) and props['c']
    assert isinstance(props['d'], bool) and props['d']
    assert isinstance(props['e'], bool) and not props['e']
    assert isinstance(props['f'], bool) and not props['f']
    assert props['g'] is None
    assert props['h'] == ''
    assert props['i'] == ConnectionMessageBased.LF
    assert props['j'] == ConnectionMessageBased.CR
    assert props['k'] == ConnectionMessageBased.CR + ConnectionMessageBased.LF
    assert props['l'] == 'some text'
    assert props['m'] == 'D:\\Data\\'


def test_encoding():

    IS_PYTHON2 = sys.version_info[0] == 2
    if IS_PYTHON2:
        reload(sys)  # required for the sys.setdefaultencoding() calls below

    print('')
    for cfg in ['utf8_txt.xml', 'cp1252_txt.xml', 'xlsx.xml']:
        db = Config(os.path.join(os.path.dirname(__file__), 'db_encoding_' + cfg)).database()

        if IS_PYTHON2:
            if cfg.startswith('cp1252'):
                sys.setdefaultencoding('cp1252')  # a legacy encoding used by Microsoft Windows
            elif cfg.startswith('utf8'):
                sys.setdefaultencoding('utf-8')

        print(db.path)

        # test printing the database records
        for r in db.records():
            print(r)
            r.to_dict()
        for r in db.connections():
            print(r)
            r.to_dict()

        assert db.records(manufacturer='Kepco*')[0].manufacturer == u'Kepco and \u201cTMK\u201d shunt'
        assert db.records(model='MFF101/M')[0].description == u'Motorized Filter Flip Mount for \xd825mm Optics'

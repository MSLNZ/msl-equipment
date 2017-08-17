import os

import pytest

from msl.equipment.config import Config


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

import sys

import pytest

from msl.equipment import EquipmentRecord, ConnectionRecord, MSLConnectionError
from msl.equipment.connection_message_based import ConnectionMessageBased


def test_termination_changed():
    c = ConnectionMessageBased(EquipmentRecord(connection=ConnectionRecord()))

    c.encoding = 'cp1252'

    assert isinstance(c.read_termination, bytes)
    assert isinstance(c.write_termination, bytes)
    assert c.read_termination == b'\n'
    assert c.write_termination == b'\r\n'

    c.encoding = 'utf-8'

    term = 'xxx'
    c.read_termination = term
    c.write_termination = term
    assert isinstance(c.read_termination, bytes)
    assert isinstance(c.write_termination, bytes)
    assert c.read_termination == term.encode()
    assert c.write_termination == term.encode()

    term = b'yyy'
    c.read_termination = term
    c.write_termination = term
    assert isinstance(c.read_termination, bytes)
    assert isinstance(c.write_termination, bytes)
    assert c.read_termination == term
    assert c.write_termination == term

    c.read_termination = None
    c.write_termination = None
    c.encoding = 'ascii'
    assert c.read_termination is None
    assert c.write_termination is None

    term = 'zzz'.encode('ascii')
    c.read_termination = term
    c.write_termination = term
    assert isinstance(c.read_termination, bytes)
    assert isinstance(c.write_termination, bytes)
    assert c.read_termination == term
    assert c.write_termination == term

    c.read_termination = bytes(bytearray([13, 10]))
    c.write_termination = bytes(bytearray([13]))
    assert isinstance(c.read_termination, bytes)
    assert isinstance(c.write_termination, bytes)
    assert c.read_termination == b'\r\n'
    assert c.write_termination == b'\r'


def test_termination_converted_to_bytes():
    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='COM6',
            backend='MSL',
            properties={'termination': 'xyz'}
        )
    )
    assert record.connection.properties['termination'] == b'xyz'


def test_encoding_errors():
    cmb = ConnectionMessageBased(EquipmentRecord(connection=ConnectionRecord()))

    assert cmb.encoding_errors == 'strict'

    allowed = ['strict', 'ignore', 'replace', 'xmlcharrefreplace', 'backslashreplace']
    if sys.version_info[:2] > (2, 7):
        allowed.append('namereplace')

    for value in allowed:
        cmb.encoding_errors = value
        assert cmb.encoding_errors == value

    for value in allowed:
        cmb.encoding_errors = value.upper()
        assert cmb.encoding_errors == value

    for item in ['doesnotexist', None, '', 888]:
        with pytest.raises(MSLConnectionError):
            cmb.encoding_errors = item

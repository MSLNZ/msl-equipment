from msl.equipment import EquipmentRecord
from msl.equipment.connection_message_based import ConnectionMessageBased


def test_termination_changed():
    c = ConnectionMessageBased(EquipmentRecord())

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

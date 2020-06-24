from msl.equipment.connection_prologix import (
    _parse_address,
    ConnectionPrologix,
)
from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.connection_socket import ConnectionSocket
from msl.equipment.connection_message_based import ConnectionMessageBased


def test_parse_address():

    cls, name, primary, secondary = _parse_address('Prologix::192.168.1.110::1234::6')
    assert cls == ConnectionSocket
    assert name == '192.168.1.110'
    assert primary == '6'
    assert secondary is None

    cls, name, primary, secondary = _parse_address('Prologix::192.168.1.110::1234::6::112')
    assert cls == ConnectionSocket
    assert name == '192.168.1.110'
    assert primary == '6'
    assert secondary == '112'

    cls, name, primary, secondary = _parse_address('Prologix::COM2::6')
    assert cls == ConnectionSerial
    assert name == 'COM2'
    assert primary == '6'
    assert secondary is None

    cls, name, primary, secondary = _parse_address('Prologix::COM2::6::112')
    assert cls == ConnectionSerial
    assert name == 'COM2'
    assert primary == '6'
    assert secondary == '112'

    cls, name, primary, secondary = _parse_address('Prologix::/dev/pts/1::2')
    assert cls == ConnectionSerial
    assert name == '/dev/pts/1'
    assert primary == '2'
    assert secondary is None

    cls, name, primary, secondary = _parse_address('PROLOGIX::/dev/ttyS1::16::100')
    assert cls == ConnectionSerial
    assert name == '/dev/ttyS1'
    assert primary == '16'
    assert secondary == '100'

    cls, name, primary, secondary = _parse_address('Prologix::/dev/ttyUSB0::16::96')
    assert cls == ConnectionSerial
    assert name == '/dev/ttyUSB0'
    assert primary == '16'
    assert secondary == '96'


def test_connection_message_based_attributes():
    cp = dir(ConnectionPrologix)
    for attr in dir(ConnectionMessageBased):
        if attr.startswith('_') or attr in ['CR', 'LF', 'raise_timeout']:
            continue
        assert attr in cp

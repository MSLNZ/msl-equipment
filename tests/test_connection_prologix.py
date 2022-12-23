from msl.equipment.connection_message_based import ConnectionMessageBased
from msl.equipment.connection_prologix import ConnectionPrologix
from msl.equipment.connection_prologix import find_prologix
from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.connection_socket import ConnectionSocket


def test_parse_address():
    for item in ['', 'Prologix', 'Prologix::', 'Prologix::COM2', 'Prologics::COM2::6',
                 'COM6', 'SDK::filename.dll', 'SOCKET::1.2.3.4::1234', 'Prologix::COM 2::20']:
        assert ConnectionPrologix.parse_address(item) is None

    info = ConnectionPrologix.parse_address('Prologix::COM1::1')
    assert info['class'] == ConnectionSerial
    assert info['name'] == 'COM1'
    assert info['pad'] == 1
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::COM2::2::96')
    assert info['class'] == ConnectionSerial
    assert info['name'] == 'COM2'
    assert info['pad'] == 2
    assert info['sad'] == 96

    info = ConnectionPrologix.parse_address('Prologix::COM3::GPIB::1')
    assert info['class'] == ConnectionSerial
    assert info['name'] == 'COM3'
    assert info['pad'] == 1
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::COM4::GPIB0::7')
    assert info['class'] == ConnectionSerial
    assert info['name'] == 'COM4'
    assert info['pad'] == 7
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::COM5::GPIB1::25::96')
    assert info['class'] == ConnectionSerial
    assert info['name'] == 'COM5'
    assert info['pad'] == 25
    assert info['sad'] == 96

    info = ConnectionPrologix.parse_address('Prologix::/dev/ttyS0::20')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/ttyS0'
    assert info['pad'] == 20
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::/dev/ttyS1::20::115')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/ttyS1'
    assert info['pad'] == 20
    assert info['sad'] == 115

    info = ConnectionPrologix.parse_address('Prologix::/dev/ttyS2::GPIB::3')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/ttyS2'
    assert info['pad'] == 3
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::/dev/ttyS3::GPIB0::11')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/ttyS3'
    assert info['pad'] == 11
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::/dev/ttyS0::GPIB2::10::100')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/ttyS0'
    assert info['pad'] == 10
    assert info['sad'] == 100

    info = ConnectionPrologix.parse_address('Prologix::192.168.1.100::1234::12')
    assert info['class'] == ConnectionSocket
    assert info['name'] == '192.168.1.100'
    assert info['pad'] == 12
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::192.168.1.100::1234::1::96')
    assert info['class'] == ConnectionSocket
    assert info['name'] == '192.168.1.100'
    assert info['pad'] == 1
    assert info['sad'] == 96

    info = ConnectionPrologix.parse_address('Prologix::192.168.1.100::1234::GPIB::1')
    assert info['class'] == ConnectionSocket
    assert info['name'] == '192.168.1.100'
    assert info['pad'] == 1
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::192.168.1.100::1234::GPIB0::22')
    assert info['class'] == ConnectionSocket
    assert info['name'] == '192.168.1.100'
    assert info['pad'] == 22
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::192.168.1.100::1234::GPIB1::17::117')
    assert info['class'] == ConnectionSocket
    assert info['name'] == '192.168.1.100'
    assert info['pad'] == 17
    assert info['sad'] == 117

    info = ConnectionPrologix.parse_address('Prologix::domainname::1234::4')
    assert info['class'] == ConnectionSocket
    assert info['name'] == 'domainname'
    assert info['pad'] == 4
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::domainname::1234::1::96')
    assert info['class'] == ConnectionSocket
    assert info['name'] == 'domainname'
    assert info['pad'] == 1
    assert info['sad'] == 96

    info = ConnectionPrologix.parse_address('Prologix::dom.ain.name::1234::GPIB::1')
    assert info['class'] == ConnectionSocket
    assert info['name'] == 'dom.ain.name'
    assert info['pad'] == 1
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::dom.ain.name::1234::GPIB0::2')
    assert info['class'] == ConnectionSocket
    assert info['name'] == 'dom.ain.name'
    assert info['pad'] == 2
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::dom.ain.name::1234::GPIB1::3::121')
    assert info['class'] == ConnectionSocket
    assert info['name'] == 'dom.ain.name'
    assert info['pad'] == 3
    assert info['sad'] == 121

    info = ConnectionPrologix.parse_address('Prologix::192.168.1.110::1234::6')
    assert info['class'] == ConnectionSocket
    assert info['name'] == '192.168.1.110'
    assert info['pad'] == 6
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::192.168.1.110::1234::6::112')
    assert info['class'] == ConnectionSocket
    assert info['name'] == '192.168.1.110'
    assert info['pad'] == 6
    assert info['sad'] == 112

    info = ConnectionPrologix.parse_address('Prologix::COM2::6')
    assert info['class'] == ConnectionSerial
    assert info['name'] == 'COM2'
    assert info['pad'] == 6
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('Prologix::COM2::6::112')
    assert info['class'] == ConnectionSerial
    assert info['name'] == 'COM2'
    assert info['pad'] == 6
    assert info['sad'] == 112

    info = ConnectionPrologix.parse_address('Prologix::/dev/pts/1::1')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/pts/1'
    assert info['pad'] == 1
    assert info['sad'] is None

    info = ConnectionPrologix.parse_address('PROLOGIX::/dev/ttyS1::16::100')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/ttyS1'
    assert info['pad'] == 16
    assert info['sad'] == 100

    info = ConnectionPrologix.parse_address('ProLOgiX::/dev/ttyS0::16::96')
    assert info['class'] == ConnectionSerial
    assert info['name'] == '/dev/ttyS0'
    assert info['pad'] == 16
    assert info['sad'] == 96


def test_connection_message_based_attributes():
    # ConnectionPrologix must have the same public attributes as ConnectionMessageBased
    cp = dir(ConnectionPrologix)
    for attr in dir(ConnectionMessageBased):
        if attr.startswith('_') or attr in ['CR', 'LF', 'raise_timeout']:
            continue
        assert attr in cp


def test_find_prologix():
    for ipv4, device in find_prologix().items():
        assert isinstance(ipv4, tuple)
        assert device['description']
        for address in device['addresses']:
            assert address.startswith('Prologix::')
            assert address.endswith('::1234::<GPIB address>')


import os
import time
import threading

try:
    import pty
except ImportError:
    pty = None

import pytest

from msl.equipment import EquipmentRecord, ConnectionRecord, Backend, MSLConnectionError
from msl.equipment.connection_serial import ConnectionSerial


def echo_server(port, term):
    while True:
        data = bytearray()
        while not data.endswith(term):
            data.extend(os.read(port, 1))

        if data.startswith(b'SHUTDOWN'):
            break

        os.write(port, data)


@pytest.mark.skipif(pty is None, reason='pty is not available')
def test_connection_serial_read():

    term = b'\r\n'

    # simulate a Serial port
    primary, secondary = pty.openpty()

    thread = threading.Thread(target=echo_server, args=(primary, term))
    thread.daemon = True
    thread.start()

    time.sleep(0.5)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='ASRL' + os.ttyname(secondary),
            backend=Backend.MSL,
            properties={
                'read_termination': term,
                'write_termination': term,
                'timeout': 25,
                'max_read_size': 1 << 16,
            },
        )
    )

    dev = record.connect()

    assert dev.read_termination == term
    assert dev.write_termination == term

    dev.write('hello')
    assert dev.read() == 'hello\r\n'

    n = dev.write('hello')
    assert dev.read(n) == 'hello\r\n'

    dev.write('x'*4096)
    assert dev.read() == 'x'*4096 + term.decode()

    n = dev.write('123.456')
    with pytest.raises(MSLConnectionError):
        dev.read(n+1)

    with pytest.raises(MSLConnectionError, match=r'max_read_size is 65536 bytes, requesting 65537 bytes'):
        dev.read(dev.max_read_size+1)  # requesting more bytes than are maximally allowed

    dev.max_read_size = 10
    dev.write(b'a'*999)
    with pytest.raises(MSLConnectionError, match=r'RuntimeError: len\(message\) \[11\] > max_read_size \[10\]'):
        dev.read()  # requesting more bytes than are maximally allowed
    dev.max_read_size = 1 << 16
    assert dev.read() == ('a' * (999 - 11)) + term.decode()  # clear the buffer

    msg = 'a' * (dev.max_read_size - len(term))
    dev.write(msg)
    assert dev.read() == msg + term.decode()

    dev.write(b'021.3' + term + b',054.2')
    assert dev.read() == '021.3\r\n'  # read until first `term`
    assert dev.read() == ',054.2\r\n'  # read until second `term`

    dev.write(b'021.3' + term + b',054.2' + term)
    assert dev.read(1) == '0'
    assert dev.read(3) == '21.'
    assert dev.read(2) == '3\r'
    assert dev.read(2) == '\n,'
    assert dev.read(1) == '0'
    assert dev.read(1) == '5'
    assert dev.read(1) == '4'
    assert dev.read() == '.2\r\n'

    dev.write('SHUTDOWN')


@pytest.mark.skipif(pty is None, reason='pty is not available')
def test_connection_serial_timeout():

    term = b'\r\n'

    # simulate a Serial port
    primary, secondary = pty.openpty()

    thread = threading.Thread(target=echo_server, args=(primary, term))
    thread.daemon = True
    thread.start()

    time.sleep(0.5)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='ASRL' + os.ttyname(secondary),
            backend=Backend.MSL,
            properties={
                'termination': term,
                'timeout': 21,
            },
        )
    )

    dev = record.connect()

    assert dev.timeout == 21
    assert dev.serial.timeout == 21
    assert dev.serial.write_timeout == 21

    dev.timeout = None
    assert dev.timeout is None
    assert dev.serial.timeout is None
    assert dev.serial.write_timeout is None

    dev.timeout = 10
    assert dev.timeout == 10
    assert dev.serial.timeout == 10
    assert dev.serial.write_timeout == 10

    dev.write('SHUTDOWN')


def test_parse_address():

    for a in ['', 'ASRL', 'COM', 'LPT', 'ASRLCOM', 'XXXX4', 'ABC2', 'COMx'
              'GPIB0::2', 'SDK::filename.so', 'SOCKET::192.168.1.100::5000', 'Prologix::COM6']:
        assert ConnectionSerial.parse_address(a) is None

    assert 'COM1' == ConnectionSerial.parse_address('COM1')['port']
    assert 'COM2' == ConnectionSerial.parse_address('ASRL2')['port']
    assert 'COM3' == ConnectionSerial.parse_address('ASRLCOM3')['port']
    assert 'COM1' == ConnectionSerial.parse_address('com1')['port']
    assert 'COM2' == ConnectionSerial.parse_address('asrl2')['port']
    assert 'COM3' == ConnectionSerial.parse_address('asrl3')['port']
    assert 'COM12' == ConnectionSerial.parse_address('COM12::INSTR')['port']
    assert 'COM2' == ConnectionSerial.parse_address('asrl2::instr')['port']
    assert 'COM30' == ConnectionSerial.parse_address('ASRLcom30::instr')['port']

    assert '/dev/ttyS0' == ConnectionSerial.parse_address('COM/dev/ttyS0')['port']
    assert '/dev/ttyS1' == ConnectionSerial.parse_address('ASRL/dev/ttyS1')['port']
    assert '/dev/ttyS2' == ConnectionSerial.parse_address('ASRLCOM/dev/ttyS2')['port']
    assert '/dev/pts/12' == ConnectionSerial.parse_address('COM/dev/pts/12')['port']
    assert '/dev/pts/12' == ConnectionSerial.parse_address('ASRL/dev/pts/12::INSTR')['port']
    assert '/dev/pts/1' == ConnectionSerial.parse_address('ASRLCOM/dev/pts/1::INSTR')['port']

    assert '/dev/ttyUSB0' == ConnectionSerial.parse_address('COM/dev/ttyUSB0')['port']
    assert '/dev/ttyUSB10' == ConnectionSerial.parse_address('COM/dev/ttyUSB10::INSTR')['port']
    assert '/dev/ttyUSB1' == ConnectionSerial.parse_address('ASRL/dev/ttyUSB1')['port']
    assert '/dev/ttyUSB0' == ConnectionSerial.parse_address('ASRL/dev/ttyUSB0::INSTR')['port']
    assert '/dev/ttyUSB2' == ConnectionSerial.parse_address('ASRLCOM/dev/ttyUSB2')['port']
    assert '/dev/ttyUSB2' == ConnectionSerial.parse_address('ASRLCOM/dev/ttyUSB2::INSTR')['port']

    assert 'COM3' == ConnectionSerial.parse_address('Prologix::COM3::6')['port']
    assert 'COM3' == ConnectionSerial.parse_address('Prologix::ASRL3::6::112')['port']
    assert 'COM7' == ConnectionSerial.parse_address('Prologix::ASRLCOM7::6::112')['port']
    assert '/dev/ttyS2' == ConnectionSerial.parse_address('Prologix::/dev/ttyS2::6')['port']
    assert '/dev/ttyUSB1' == ConnectionSerial.parse_address('PROLOGIX::/dev/ttyUSB1::1::96')['port']
    assert '/dev/pts/1' == ConnectionSerial.parse_address('ProLOgix::/dev/pts/1::2')['port']

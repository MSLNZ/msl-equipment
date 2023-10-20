from __future__ import annotations

import os
import threading
import time

try:
    import pty
except ImportError:
    pty = None

import pytest

from msl.equipment import Backend
from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord
from msl.equipment import MSLConnectionError
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


@pytest.mark.parametrize(
    'address',
    ['', 'ASRL', 'COM', 'LPT', 'ASRLCOM', 'XXXX4', 'ABC2', 'COMx', 'GPIB0::2',
     'SDK::filename.so', 'SOCKET::192.168.1.100::5000', 'Prologix::COM6'])
def test_parse_address_invalid(address):
    assert ConnectionSerial.parse_address(address) is None


@pytest.mark.parametrize(
    'address, expected',
    [
        ('COM1', 'COM1'),
        ('ASRL2', 'COM2'),
        ('ASRLCOM3', 'COM3'),
        ('com11', 'COM11'),
        ('asrl22', 'COM22'),
        ('asrlcom10', 'COM10'),
        ('COM12::INSTR', 'COM12'),
        ('asrl2::instr', 'COM2'),
        ('ASRLcom30::instr', 'COM30'),
        ('COM/dev/ttyS0', '/dev/ttyS0'),
        ('ASRL/dev/ttyS1', '/dev/ttyS1'),
        ('ASRLCOM/dev/ttyS2', '/dev/ttyS2'),
        ('COM/dev/pts/12', '/dev/pts/12'),
        ('ASRL/dev/pts/12::INSTR', '/dev/pts/12'),
        ('ASRLCOM/dev/pts/1::INSTR', '/dev/pts/1'),
        ('COM/dev/ttyUSB0', '/dev/ttyUSB0'),
        ('COM/dev/ttyUSB10::INSTR', '/dev/ttyUSB10'),
        ('ASRL/dev/ttyUSB1', '/dev/ttyUSB1'),
        ('ASRL/dev/ttyUSB0::INSTR', '/dev/ttyUSB0'),
        ('COM/dev/symlink_name', '/dev/symlink_name'),
        ('ASRL/dev/symlink_name', '/dev/symlink_name'),
        ('ASRLCOM/dev/symlink_name', '/dev/symlink_name'),
        ('ASRLCOM/dev/ttyUSB2', '/dev/ttyUSB2'),
        ('ASRLCOM/dev/ttyUSB2::INSTR', '/dev/ttyUSB2'),
        ('Prologix::COM3::6', 'COM3'),
        ('Prologix::ASRL3::6::112', 'COM3'),
        ('Prologix::ASRLCOM7::6::112', 'COM7'),
        ('Prologix::/dev/ttyS2::6', '/dev/ttyS2'),
        ('PROLOGIX::/dev/ttyUSB1::1::96', '/dev/ttyUSB1'),
        ('ProLOgix::/dev/pts/1::2', '/dev/pts/1'),
        ('Prologix::/dev/symlink_name::6', '/dev/symlink_name'),
        ('ASRL/dev/cu.Bluetooth-Incoming-Port::INSTR', '/dev/cu.Bluetooth-Incoming-Port'),
        ('ASRL/dev/cu.usbmodemHIDPC1', '/dev/cu.usbmodemHIDPC1'),
        ('ASRL/dev/cu.usbserial-FTE1XGBL::INSTR', '/dev/cu.usbserial-FTE1XGBL'),
        ('ASRL/dev/cu.usbmodem1421401::INSTR', '/dev/cu.usbmodem1421401'),
    ])
def test_parse_address_valid(address, expected):
    assert ConnectionSerial.parse_address(address)['port'] == expected

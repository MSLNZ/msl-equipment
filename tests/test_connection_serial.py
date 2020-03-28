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


@pytest.mark.skipif(pty is None, reason='pty is not available')
def test_connection_serial_read():

    term = b'\r\n'

    def echo_server(port):
        while True:
            data = bytearray()
            while not data.endswith(term):
                data.extend(os.read(port, 1))

            if data.startswith(b'SHUTDOWN'):
                break

            os.write(port, data)

    # simulate a Serial port
    master, slave = pty.openpty()

    thread = threading.Thread(target=echo_server, args=(master,))
    thread.start()

    time.sleep(0.5)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='ASRL::' + os.ttyname(slave),
            backend=Backend.MSL,
            properties={
                'read_termination': term,
                'write_termination': term,
                'timeout': 25,
            },
        )
    )

    dev = record.connect()

    assert dev.read_termination == term
    assert dev.write_termination == term

    dev.write('hello')
    assert dev.read() == 'hello'

    n = dev.write('hello')
    assert dev.read(n) == 'hello' + term.decode()

    dev.write('x'*4096)
    assert dev.read() == 'x'*4096

    n = dev.write('123.456')
    with pytest.raises(MSLConnectionError):
        dev.read(n+1)

    with pytest.raises(MSLConnectionError):
        dev.read(dev.max_read_size+1)  # requesting more bytes than are maximally allowed

    msg = 'a' * (dev.max_read_size - len(term))
    dev.write(msg)
    assert dev.read() == msg

    dev.write(b'021.3' + term + b',054.2')
    assert dev.read() == '021.3'  # read until first `term`
    assert dev.read() == ',054.2'  # read until second `term`

    dev.write('SHUTDOWN')


def test_port_from_address():

    for a in ['ASRL', 'COM', 'LPT', 'ASRLCOM', 'Prologix::COM::', '', 'SERIAL::XXX4', 'ABC2'
              'GPIB::2::INSTR', 'SDK::filename.so', 'SOCKET::192.168.1.100::5000']:
        assert ConnectionSerial.port_from_address(a) is None

    assert 'COM15' == ConnectionSerial.port_from_address('ASRL15')
    assert 'COM3' == ConnectionSerial.port_from_address('ASRL3::INSTR')
    assert 'COM3' == ConnectionSerial.port_from_address('ASRL3::instr')
    assert 'COM10' == ConnectionSerial.port_from_address('COM10')
    assert 'COM11' == ConnectionSerial.port_from_address('SERIAL::COM11')
    assert 'COM3' == ConnectionSerial.port_from_address('LPT3')
    assert 'COM7' == ConnectionSerial.port_from_address('ASRLCOM7')
    assert '/dev/pts/12' == ConnectionSerial.port_from_address('SERIAL::/dev/pts/12')
    assert '/dev/ttyUSB0' == ConnectionSerial.port_from_address('ASRL::/dev/ttyUSB0::INSTR')
    assert '/dev/ttyS1' == ConnectionSerial.port_from_address('ASRLCOM::/dev/ttyS1')
    assert 'COM3' == ConnectionSerial.port_from_address('Prologix::COM3::6')
    assert 'COM3' == ConnectionSerial.port_from_address('Prologix::ASRL3::6::112')
    assert '/dev/ttyUSB0' == ConnectionSerial.port_from_address('Prologix::/dev/ttyUSB0::6')
    assert '/dev/ttyS1' == ConnectionSerial.port_from_address('PROLOGIX::/dev/ttyS1::6::96')
    assert '/dev/pts/1' == ConnectionSerial.port_from_address('Prologix::/dev/pts/1::2')

import os
import time
import threading

try:
    import pty
except ImportError:
    pty = None

import pytest

from msl.equipment import EquipmentRecord, ConnectionRecord, Backend, MSLConnectionError


@pytest.mark.skipif(pty is None, reason='pty is not available')
def test_connection_serial_read():

    term = b'\r\n'

    def echo_server(port):
        data = bytearray()
        while True:
            while not data.endswith(term):
                data.extend(os.read(port, 1))

            if data.startswith(b'SHUTDOWN'):
                break

            os.write(port, data)
            data.clear()

    # simulate a Serial port
    master, slave = pty.openpty()

    thread = threading.Thread(target=echo_server, args=(master,))
    thread.start()

    time.sleep(0.1)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='ASRL::' + os.ttyname(slave),
            backend=Backend.MSL,
            properties={
                'read_termination': term,
                'write_termination': term,
                'timeout': 5,
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

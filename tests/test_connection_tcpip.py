import time
import socket
import threading

import pytest

from msl.loadlib.utils import get_available_port

from msl.equipment import EquipmentRecord, ConnectionRecord, Backend, MSLTimeoutError, MSLConnectionError


def test_tcpip_socket_read():

    address = '127.0.0.1'
    port = get_available_port()
    term = b'\r\n'

    def echo_server():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((address, port))
        s.listen(1)
        conn, _ = s.accept()

        while True:
            data = bytearray()
            while not data.endswith(term):
                data.extend(conn.recv(4096))

            if data.startswith(b'SHUTDOWN'):
                break

            conn.sendall(data)

        conn.close()
        s.close()

    t = threading.Thread(target=echo_server)
    t.start()

    time.sleep(0.1)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP::{}::{}::SOCKET'.format(address, port),
            backend=Backend.MSL,
            properties=dict(
                read_termination=term,
                write_termination=term,
                timeout=5
            ),
        )
    )

    dev = record.connect()

    assert dev.read_termination == term
    assert dev.write_termination == term

    dev.write('hello')
    assert dev.read() == 'hello'

    n = dev.write('hello')
    assert dev.read(n) == 'hello' + term.decode()  # specified `size` so `term` is not removed

    n = dev.write(b'021.3' + term + b',054.2')
    assert dev.read(n) == '021.3' + term.decode() + ',054.2' + term.decode()  # `term` is not removed

    dev.write(b'021.3' + term + b',054.2')
    assert dev.read(3) == '021'
    assert dev.read(5) == '.3' + term.decode() + ','
    assert dev.read() == '054.2'  # read the rest -- removes the `term` at the end

    dev.write(b'021.3' + term + b',054.2')
    assert dev.read() == '021.3'  # read until first `term`
    assert dev.read() == ',054.2'  # read until second `term`

    n = dev.write('12345')
    assert n == 7
    with pytest.raises(MSLTimeoutError):
        dev.read(n+1)  # read more bytes than are available
    assert dev.read(n) == '12345' + term.decode()
    assert len(dev.byte_buffer) == 0

    msg = 'a' * (dev.max_read_size - len(term))
    dev.write(msg)
    assert dev.read() == msg

    dev.write(b'x'*1024 + term + b'y'*2048)
    assert dev.read() == 'x'*1024  # read until `term`
    assert len(dev.byte_buffer) == 2048 + len(term)
    dev.max_read_size = 2000
    with pytest.raises(MSLConnectionError):
        dev.read(2048)  # requesting more bytes than are maximally allowed

    dev.write('SHUTDOWN')

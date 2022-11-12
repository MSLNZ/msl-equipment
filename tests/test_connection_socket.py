import time
import socket
import threading

import pytest

from msl.loadlib.utils import get_available_port

from msl.equipment import EquipmentRecord, ConnectionRecord, Backend, MSLTimeoutError, MSLConnectionError
from msl.equipment.connection_socket import ConnectionSocket


def echo_server_tcp(address, port, term):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((address, port))
    s.listen(2)
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


def echo_server_udp(address, port, term):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((address, port))

    while True:
        data = bytearray()
        while not data.endswith(term):
            msg, addr = s.recvfrom(4096)
            data.extend(msg)

        if data.startswith(b'SHUTDOWN'):
            break

        s.sendto(data, addr)

    s.close()


def test_tcp_socket_read():

    address = '127.0.0.1'
    port = get_available_port()
    term = b'\r\n'

    t = threading.Thread(target=echo_server_tcp, args=(address, port, term))
    t.daemon = True
    t.start()

    time.sleep(0.1)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='SOCKET::{}::{}'.format(address, port),
            backend=Backend.MSL,
            properties=dict(
                termination=term,  # sets both read_termination and write_termination
                timeout=30
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


def test_tcp_socket_timeout():

    address = '127.0.0.1'
    port = get_available_port()
    write_termination = b'\n'

    t = threading.Thread(target=echo_server_tcp, args=(address, port, write_termination))
    t.daemon = True
    t.start()

    time.sleep(0.1)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP::{}::{}::SOCKET'.format(address, port),  # use PyVISA's address convention
            backend=Backend.MSL,
            properties=dict(
                write_termination=write_termination,
                timeout=7
            ),
        )
    )

    dev = record.connect()
    assert dev.timeout == 7
    assert dev.socket.gettimeout() == 7

    dev.timeout = None
    assert dev.timeout is None
    assert dev.socket.gettimeout() is None

    dev.timeout = 0.1
    assert dev.timeout == 0.1
    assert dev.socket.gettimeout() == 0.1

    dev.timeout = 0
    assert dev.timeout is None
    assert dev.socket.gettimeout() is None

    dev.timeout = -1
    assert dev.timeout is None
    assert dev.socket.gettimeout() is None

    dev.timeout = -12345
    assert dev.timeout is None
    assert dev.socket.gettimeout() is None

    dev.timeout = 10
    assert dev.timeout == 10
    assert dev.socket.gettimeout() == 10

    dev.write('SHUTDOWN')


def test_udp_socket_read():

    address = '127.0.0.1'
    port = get_available_port()
    term = b'\r\n'

    t = threading.Thread(target=echo_server_udp, args=(address, port, term))
    t.daemon = True
    t.start()

    time.sleep(0.1)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='UDP::{}::{}'.format(address, port),
            backend=Backend.MSL,
            properties=dict(
                termination=term,  # sets both read_termination and write_termination
                timeout=30
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

    dev.write('SHUTDOWN')


def test_wrong_socket_type():

    address = '127.0.0.1'
    port = get_available_port()
    term = b'\r\n'

    t = threading.Thread(target=echo_server_udp, args=(address, port, term))
    t.daemon = True
    t.start()

    time.sleep(0.1)  # allow some time for the echo server to start

    with pytest.raises(MSLConnectionError):
        EquipmentRecord(
            connection=ConnectionRecord(
                address='TCP::{}::{}'.format(address, port),  # trying TCP for a UDP server
                backend=Backend.MSL,
                properties=dict(
                    termination=term,
                    timeout=5
                ),
            )
        ).connect()

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='UDP::{}::{}'.format(address, port),
            backend=Backend.MSL,
            properties=dict(
                termination=term,
                timeout=5
            ),
        )
    )

    # use the correct socket type to shutdown the server
    dev = record.connect()
    dev.write('SHUTDOWN')


def test_parse_address():

    #
    # different number of digits in IP address
    #
    info = ConnectionSocket.parse_address('SOCKET::1.2.3.4::1234')
    assert info['host'] == '1.2.3.4'
    assert info['port'] == 1234

    info = ConnectionSocket.parse_address('SOCKET::11.22.33.44::1234')
    assert info['host'] == '11.22.33.44'
    assert info['port'] == 1234

    info = ConnectionSocket.parse_address('SOCKET::111.222.103.231::1234')
    assert info['host'] == '111.222.103.231'
    assert info['port'] == 1234

    # different interface prefix
    for prefix in ('TCP', 'UDP', 'SOCKET'):
        info = ConnectionSocket.parse_address(prefix + '::192.168.1.100::1234')
        assert info['host'] == '192.168.1.100'
        assert info['port'] == 1234

        info = ConnectionSocket.parse_address(prefix + '::my.hostname.com::8080::SOCKET')
        assert info['host'] == 'my.hostname.com'
        assert info['port'] == 8080

        info = ConnectionSocket.parse_address(prefix + '::192.168.1.100::54123::SOCKET')
        assert info['host'] == '192.168.1.100'
        assert info['port'] == 54123

        info = ConnectionSocket.parse_address(prefix + '::172.16.14.100::5000::some::extra::stuff::added')
        assert info['host'] == '172.16.14.100'
        assert info['port'] == 5000

        assert ConnectionSocket.parse_address(prefix) is None
        assert ConnectionSocket.parse_address(prefix + '::no.port.specified') is None
        assert ConnectionSocket.parse_address(prefix + '::no.port.specified::') is None
        assert ConnectionSocket.parse_address(prefix + '::172.16.14.1::not_an_int') is None

    assert ConnectionSocket.parse_address('') is None
    assert ConnectionSocket.parse_address('COM5') is None
    assert ConnectionSocket.parse_address('ASRL::COM11::INSTR') is None
    assert ConnectionSocket.parse_address('GPIB0::1') is None
    assert ConnectionSocket.parse_address('GPIB0::1::2') is None

    #
    # check compatibility with the IVI library: TCPIP[board]::host address::port::SOCKET
    #

    assert ConnectionSocket.parse_address('TCPIP::full.domain.name::1234') is None
    assert ConnectionSocket.parse_address('TCPIP::full.domain.name::1234::INVALID') is None
    assert ConnectionSocket.parse_address('TCPIP::192.168.1.100::1234::INSTR') is None

    info = ConnectionSocket.parse_address('TCPIP::full.domain.name::1234::SOCKET')
    assert info['host'] == 'full.domain.name'
    assert info['port'] == 1234

    info = ConnectionSocket.parse_address('TCPIP0::1.2.3.4::12345::SOCKET')
    assert info['host'] == '1.2.3.4'
    assert info['port'] == 12345

    info = ConnectionSocket.parse_address('TCPIP2::1.22.3.100::12345::SOCKET')
    assert info['host'] == '1.22.3.100'
    assert info['port'] == 12345

    info = ConnectionSocket.parse_address('TCPIP10::192.10.126.3::1234::SOCKET')
    assert info['host'] == '192.10.126.3'
    assert info['port'] == 1234

    #
    # check that an address for the Prologix interface is valid
    #

    info = ConnectionSocket.parse_address('Prologix::192.168.1.70::1234::6')
    assert info['host'] == '192.168.1.70'
    assert info['port'] == 1234

    info = ConnectionSocket.parse_address('PROLOGIX::hostname::1234::6')
    assert info['host'] == 'hostname'
    assert info['port'] == 1234

    info = ConnectionSocket.parse_address('ProLOgiX::full.domain.name::1234::6')
    assert info['host'] == 'full.domain.name'
    assert info['port'] == 1234

    assert ConnectionSocket.parse_address('Prologics::192.168.1.70::1234::6') is None

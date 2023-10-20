from __future__ import annotations

import socket
import sys
import threading
import time

import pytest
from msl.loadlib.utils import get_available_port

from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord
from msl.equipment import MSLConnectionError
from msl.equipment import MSLTimeoutError
from msl.equipment.connection_tcpip_hislip import ConnectionTCPIPHiSLIP
from msl.equipment.hislip import AsyncInitialize
from msl.equipment.hislip import Message
from msl.equipment.hislip import PORT


@pytest.mark.parametrize(
    'address,expected',
    [('TCPIP::dev.company.com::INSTR', None),
     ('GPIB::23', None),
     ('TCPIP::dev.company.com::hisli', None),
     ('TCPIP0::dev.company.com::instr::INSTR', None),
     ('TCPIP0::10.0.0.1::usb0[1234::5678::MYSERIAL::0]::INSTR', None),
     ('TCPIP::1.1.1.1::gpib,5::INSTR', None),
     ('TCPIP::1.1.1.1::gpib,5', None),
     ('TCPIP0::company::hislip0,port::INSTR', None),
     ('tcpip3::10.0.0.1::USB0::instr', None),
     ('SOCKET::myMachine::1234', None),
     ('TCPIP0::testMachine1::COM1,488::INSTR', None),
     ('TCPIP::1.2.3.4::HiSLIP0::INSTR', ('0', '1.2.3.4', 'HiSLIP0', PORT)),
     ('TCPIP::company::hislip1,3::INSTR', ('0', 'company', 'hislip1', 3)),
     ('tcpip::company::hislip1,30000::INSTR', ('0', 'company', 'hislip1', 30000)),
     ('TCPIP0::1.2.3.4::hislip0', ('0', '1.2.3.4', 'hislip0', PORT)),
     ('TCPIP1::company::hislip0,4880::INSTR', ('1', 'company', 'hislip0', 4880)),
     ('TCPIP2::company2::hislip1,30000::INSTR', ('2', 'company2', 'hislip1', 30000))])
def test_parse_address(address, expected):
    info = ConnectionTCPIPHiSLIP.parse_address(address)
    if expected is None:
        assert info is None
    else:
        board, host, name, port = expected
        assert info['board'] == board
        assert info['host'] == host
        assert info['name'] == name
        assert info['port'] == port


def server(address, port, action):
    # Simulate a HiSLIP server.

    # The payloads for the request/reply were determined when an instrument
    # was on the same network as the computer. The client did the following:
    # 1. Synchronous channel connects
    # 2. Initialize request
    # 3. Asynchronous channel connects
    # 4. AsyncInitialize request
    # 5. AsyncMaximumMessageSize request
    # 6. "*IDN?" query (synchronous channel)

    initialize_request = b'HS\x00\x00\x01\x00XX\x00\x00\x00\x00\x00\x00\x00\x07hislip0'

    initialize_response = b'HS\x01\x00\x01\x00\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00'

    async_initialize_request = b'HS\x11\x00\x00\x00\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00'

    async_initialize_response = b'HS\x12\x00\x00\x00XX\x00\x00\x00\x00\x00\x00\x00\x00'

    async_maximum_message_size_request = b'HS\x0f\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                                         b'\x00\x00\x00\x08\x00\x00\x00\x00\x00\x10\x00\x00'

    async_maximum_message_size_response = b'HS\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                                          b'\x00\x00\x00\x08\x00\x00\x00\x00\x00\x10\x00\x00'

    idn_request = b'HS\x07\x00\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x05*IDN?'

    idn_reply = b'HS\x07\x00\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00H' \
                b'Manufacturer of the Device,Model,Serial,X.01.23-45.67-89.ab-cd.ef-gh-ij\n' \
                b'\x00\x00\x00\x00\x00\x00'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((address, port))
    s.listen(2)
    sync_conn, _ = s.accept()  # synchronous channel connects
    data = sync_conn.recv(256)
    assert data == initialize_request
    sync_conn.sendall(initialize_response)
    async_conn, _ = s.accept()  # asynchronous channel connects
    data = async_conn.recv(256)
    assert data == async_initialize_request
    async_conn.sendall(async_initialize_response)
    data = async_conn.recv(256)
    assert data == async_maximum_message_size_request
    async_conn.sendall(async_maximum_message_size_response)
    data = sync_conn.recv(256)
    if action == 'idn':
        assert data == idn_request
        sync_conn.sendall(idn_reply)
    elif action == 'sleep':
        time.sleep(1.5)  # must be > 1
    elif action == 'bad-header':
        sync_conn.sendall(b'<16bytes')
    while True:
        # wait for asynchronous channel to disconnect
        # it disconnects before the synchronous channel
        data = async_conn.recv(256)
        if not data:
            break
    sync_conn.close()
    async_conn.close()
    s.close()


def test_protocol():
    address = '127.0.0.1'
    port = get_available_port()

    t = threading.Thread(target=server, args=(address, port, 'idn'))
    t.daemon = True
    t.start()
    time.sleep(0.1)  # allow some time for the server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP::{}::hislip0,{}'.format(address, port),
            properties={'timeout': 5}
        )
    )

    dev = record.connect()
    assert dev.port == port
    assert dev.host == address
    assert dev.timeout == 5
    assert dev.asynchronous.get_timeout() == 5
    assert dev.synchronous.get_timeout() == 5
    assert dev.lock_timeout == 0
    assert dev.read_termination is None
    assert dev.write_termination is None
    assert dev.query('*IDN?') == 'Manufacturer of the Device,Model,Serial,X.01.23-45.67-89.ab-cd.ef-gh-ij\n'

    dev.timeout = -1
    assert dev.timeout is None
    assert dev.asynchronous.get_timeout() is None
    assert dev.synchronous.get_timeout() is None

    dev.timeout = 0
    assert dev.timeout == 0.0
    assert dev.asynchronous.get_timeout() == 0.0
    assert dev.synchronous.get_timeout() == 0.0

    dev.timeout = None
    assert dev.timeout is None
    assert dev.asynchronous.get_timeout() is None
    assert dev.synchronous.get_timeout() is None

    dev.timeout = 1.1
    assert dev.timeout == 1.1
    assert dev.asynchronous.get_timeout() == 1.1
    assert dev.synchronous.get_timeout() == 1.1

    dev.lock_timeout = -2.1
    assert dev.lock_timeout == 86400.0
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.lock_timeout = None
    assert dev.lock_timeout == 86400.0
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.lock_timeout = 0
    assert dev.lock_timeout == 0.0
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.lock_timeout = 1.2
    assert dev.lock_timeout == 1.2
    assert dev.asynchronous.get_timeout() == 1.1  # gets updated during async_lock_request()
    assert dev.synchronous.get_timeout() == 1.1  # not changed, lock timeout only used for asynchronous request

    dev.disconnect()

    assert dev.asynchronous is None
    assert dev.synchronous is None


def test_exceptions():
    address = '127.0.0.1'

    # server not running
    port = get_available_port()
    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP0::{}::hislip0,{}::INSTR'.format(address, port),
            properties={'timeout': 1, 'rstrip': True}
        )
    )
    if sys.platform == 'win32':
        match = r'Timeout occurred after 1.0 second\(s\)'
    else:
        match = 'Connection refused'
    with pytest.raises(MSLConnectionError, match=match):
        record.connect()

    # server hangs during a query (after the connection is established)
    port = get_available_port()
    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP0::{}::hislip0,{}::INSTR'.format(address, port),
            properties={'timeout': 1, 'rstrip': True}
        )
    )
    t = threading.Thread(target=server, args=(address, port, 'sleep'))
    t.daemon = True
    t.start()
    time.sleep(0.1)  # allow some time for the server to start
    dev = record.connect()
    with pytest.raises(MSLTimeoutError, match=r'Timeout occurred after 1.0 second\(s\)'):
        dev.query('sleep')
    t.join()

    # server returns a bad header (after the connection is established)
    port = get_available_port()
    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP0::{}::hislip0,{}::INSTR'.format(address, port),
            properties={'timeout': 1, 'rstrip': True}
        )
    )
    t = threading.Thread(target=server, args=(address, port, 'bad-header'))
    t.daemon = True
    t.start()
    time.sleep(0.1)  # allow some time for the server to start
    dev = record.connect()
    with pytest.raises(MSLConnectionError, match='The reply header is != 16 bytes'):
        dev.query('bad-header')
    t.join()


def test_str():
    assert str(Message()) == "Message<type=None control_code=0 parameter=0 payload=b''>"
    assert repr(Message()) == "Message<type=None control_code=0 parameter=0 payload=b''>"

    msg = AsyncInitialize(4, 3, b'x'*25)
    if sys.version_info.major == 2:
        assert str(msg) == "Message<type=AsyncInitialize control_code=4 parameter=3 " \
                           "payload=xxxxxxxxxxxxxxxxxxxxxxxxx>"
    else:
        assert str(msg) == "Message<type=AsyncInitialize control_code=4 parameter=3 " \
                           "payload=b'xxxxxxxxxxxxxxxxxxxxxxxxx'>"

    msg = AsyncInitialize(payload=b'abcdefghijklmnopqrstuvwxyz'*4)
    if sys.version_info.major == 2:
        assert str(msg) == "Message<type=AsyncInitialize control_code=0 parameter=0 " \
                           "payload[104]=abcdefghijklmnopqrstuvwxy...bcdefghijklmnopqrstuvwxyz>"
    else:
        assert str(msg) == "Message<type=AsyncInitialize control_code=0 parameter=0 " \
                           "payload[104]=b'abcdefghijklmnopqrstuvwxy'...b'bcdefghijklmnopqrstuvwxyz'>"


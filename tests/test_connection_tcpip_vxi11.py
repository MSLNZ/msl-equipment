import socket
import struct
import threading
import time

import pytest
from msl.loadlib.utils import get_available_port

from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord
from msl.equipment.connection_tcpip_vxi11 import ConnectionTCPIPVXI11
from msl.equipment.vxi11 import PMAP_PORT


@pytest.mark.parametrize(
    'address,expected',
    [('TCPI::dev.company.com::INSTR', None),
     ('GPIB::23', None),
     ('TCPIP::dev.company.com::hislip::INSTR', None),
     ('TCPIP::1.2.3.4::HiSLIP0::INSTR', None),
     ('TCPIP::company::hislip1,3::INSTR', None),
     ('TCPIP0::192.168.2.100::hislip0', None),
     ('TCPIP0::dev.company.com::instr::INSTR', None),
     ('TCPIP::dev.company.com::InStR', ('0', 'dev.company.com', 'inst0')),
     ('TCPIP1::company::INSTR', ('1', 'company', 'inst0')),
     ('TCPIP0::10.0.0.1::usb0[1234::5678::MYSERIAL::0]::INSTR', ('0', '10.0.0.1', 'usb0[1234::5678::MYSERIAL::0]')),
     ('TCPIP::10.0.0.1::usb0[1234::5678::MYSERIAL::0]', ('0', '10.0.0.1', 'usb0[1234::5678::MYSERIAL::0]')),
     ('TCPIP0::myMachine::usb0[2391::1031::SN_00123::0]::INSTR', ('0', 'myMachine', 'usb0[2391::1031::SN_00123::0]')),
     ('TCPIP::10.0.0.1::instr2::INSTR', ('0', '10.0.0.1', 'instr2')),
     ('TCPIP2::10.0.0.1::instr1', ('2', '10.0.0.1', 'instr1')),
     ('TCPIP::1.1.1.1::gpib,5::INSTR', ('0', '1.1.1.1', 'gpib,5')),
     ('TCPIP10::192.168.1.100::gpib,5::iNsTr', ('10', '192.168.1.100', 'gpib,5')),
     ('tcpip3::10.0.0.1::USB0::instr', ('3', '10.0.0.1', 'USB0')),
     ('TCPIP0::123.456.0.21::gpib0,2,3', ('0', '123.456.0.21', 'gpib0,2,3')),
     ('TCPIP0::myMachine::inst0::INSTR', ('0', 'myMachine', 'inst0')),
     ('TCPIP::myMachine', ('0', 'myMachine', 'inst0')),
     ('TCPIP0::testMachine1::COM1,488::INSTR', ('0', 'testMachine1', 'COM1,488')),
     ('TCPIP0::myMachine::gpib0,2', ('0', 'myMachine', 'gpib0,2')),
     ('TCPIP0::myMachine::UsbDevice1::INSTR', ('0', 'myMachine', 'UsbDevice1'))])
def test_parse_address(address, expected):
    if expected is None:
        assert ConnectionTCPIPVXI11.parse_address(address) is None
    else:
        board, host, name = expected
        info = ConnectionTCPIPVXI11.parse_address(address)
        assert info['board'] == board
        assert info['host'] == host
        assert info['name'] == name


def rpc_server(address, prog_port):
    # Simulate an RPC server for Port Mapping.

    # The payloads for the request/reply were determined when an instrument
    # was on the same network as the computer
    request = b'\x80\x00\x008\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02' \
              b'\x00\x01\x86\xa0\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06' \
              b'\x07\xaf\x00\x00\x00\x01\x00\x00\x00\x06\x00\x00\x00\x00'

    reply = b'\x80\x00\x00\x1c\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00' \
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    reply += struct.pack('>L', prog_port)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((address, PMAP_PORT))
    s.listen(1)
    conn, _ = s.accept()
    while True:
        data = conn.recv(256)
        if data and data == request:
            conn.sendall(reply)
        else:
            break
    conn.close()
    s.close()


def rpc_program(address, prog_port):
    # Simulate a program on the RPC server.

    # The payloads for the request/reply were determined when an instrument
    # was on the same network as the computer. The client did the following:
    # 1. Created a link
    # 2. Queried "*IDN?"
    # 3. Destroyed the link

    # creating a link calls random.getrandbits(31) for the client ID so the link
    # request will always be different for 4 bytes in the middle of the message
    link_request_prefix = b'\x80\x00\x00@\x00\x00\x00\x01\x00\x00\x00\x00\x00' \
                          b'\x00\x00\x02\x00\x06\x07\xaf\x00\x00\x00\x01\x00' \
                          b'\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                          b'\x00\x00\x00\x00\x00\x00'
    link_request_suffix = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05' \
                          b'inst0\x00\x00\x00'

    link_reply = b'\x80\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00' \
                 b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                 b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02k\x00\x00\x05\xdc'

    idn_request = b'\x80\x00\x00D\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x02' \
                  b'\x00\x06\x07\xaf\x00\x00\x00\x01\x00\x00\x00\x0b\x00\x00\x00' \
                  b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                  b'\x00\x00\x00\x00\x13\x88\x00\x00\x00\x00\x00\x00\x00\x08\x00' \
                  b'\x00\x00\x05*IDN?\x00\x00\x00'

    idn_reply = b'\x80\x00\x00 \x00\x00\x00\x02\x00\x00\x00\x01\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                b'\x00\x00\x00\x00\x00\x00\x00\x00\x05'

    read_request = b'\x80\x00\x00@\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00' \
                   b'\x02\x00\x06\x07\xaf\x00\x00\x00\x01\x00\x00\x00\x0c\x00' \
                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                   b'\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x13\x88\x00' \
                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    read_reply = b'\x80\x00\x00\\\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00' \
                 b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                 b'\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x005' \
                 b'Manufacturer of the Device,Model,Serial,dd.mm.yyyy  \n' \
                 b'\x00\x00\x00'

    unlink_request = b'\x80\x00\x00,\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00' \
                     b'\x00\x02\x00\x06\x07\xaf\x00\x00\x00\x01\x00\x00\x00' \
                     b'\x17\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                     b'\x00\x00\x00\x00\x00\x00\x00\x00'

    unlink_reply = b'\x80\x00\x00\x1c\x00\x00\x00\x04\x00\x00\x00\x01\x00' \
                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                   b'\x00\x00\x00\x00\x00\x00'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((address, prog_port))
    s.listen(1)
    conn, _ = s.accept()
    while True:
        data = conn.recv(256)
        if data.startswith(link_request_prefix) and data.endswith(link_request_suffix):
            conn.sendall(link_reply)
        elif data == idn_request:
            conn.sendall(idn_reply)
        elif data == read_request:
            conn.sendall(read_reply)
        elif data == unlink_request:
            conn.sendall(unlink_reply)
        else:
            break
    conn.close()
    s.close()


def test_protocol():
    address = '127.0.0.1'
    prog_port = get_available_port()

    t1 = threading.Thread(target=rpc_server, args=(address, prog_port))
    t1.daemon = True
    t2 = threading.Thread(target=rpc_program, args=(address, prog_port))
    t2.daemon = True
    t1.start()
    t2.start()
    time.sleep(0.1)  # allow some time for the servers to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP::' + address,
            properties={'timeout': 5}
        )
    )

    dev = record.connect()
    assert dev.timeout == 5
    assert dev.lock_timeout == 0
    assert dev.read_termination is None
    assert dev.write_termination is None
    assert dev.query('*IDN?') == 'Manufacturer of the Device,Model,Serial,dd.mm.yyyy  \n'
    assert dev.byte_buffer == b'\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x02\x00' \
                              b'\x06\x07\xaf\x00\x00\x00\x01\x00\x00\x00\x0c\x00\x00' \
                              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                              b'\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x13\x88' \
                              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    dev.disconnect()

    dev.timeout = None
    assert dev._timeout is None
    assert dev._io_timeout_ms == 0

    dev.lock_timeout = None
    assert dev._lock_timeout == 0
    assert dev._lock_timeout_ms == 0

    dev.lock_timeout = 1.2
    assert dev._lock_timeout == 1.2
    assert dev._lock_timeout_ms == 1200

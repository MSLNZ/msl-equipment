import os
import subprocess
import sys
import tempfile
import time

import pytest
import zmq
from msl.loadlib.utils import get_available_port
from msl.loadlib.utils import is_port_in_use

from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord
from msl.equipment import MSLConnectionError
from msl.equipment.connection_zeromq import ConnectionZeroMQ

PORT = get_available_port()


def start_zmq_server():
    code = """import time
import zmq
PORT = %d
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind('tcp://127.0.0.1:{}'.format(PORT))
while True:
    message = socket.recv()
    if message == b'SHUTDOWN':
        break
    if message == b'sleep':
        time.sleep(0.5)
    socket.send(message)
socket.unbind('tcp://127.0.0.1:{}'.format(PORT))
context.destroy()
print('done')
""" % PORT

    path = os.path.join(tempfile.gettempdir(), 'msl_equipment_zeromq_server.py')
    with open(path, mode='wt') as f:
        f.write(code)

    p = subprocess.Popen(
        [sys.executable, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    while not is_port_in_use(PORT):
        time.sleep(0.1)

    return p, path


def cleanup_zmq_server(proc, filename):
    stdout, stderr = proc.communicate()
    assert stdout.rstrip().decode() == 'done'
    assert not stderr
    os.remove(filename)


@pytest.mark.parametrize(
    'address,expected',
    [('TCPIP::dev.company.com::INSTR', None),
     ('GPIB::23', None),
     ('SOCKET::myMachine::1234', None),
     ('TCP::127.0.0.1::5555', None),
     ('ZMQ::127.0.0.1::port', None),
     ('ZMQ::1.2.3.4::5555', ('1.2.3.4', 5555)),
     ('zmq::company::12345', ('company', 12345)),
     ('ZmQ::dev.company.org::111', ('dev.company.org', 111))])
def test_parse_address(address, expected):
    info = ConnectionZeroMQ.parse_address(address)
    if expected is None:
        assert info is None
    else:
        host, port = expected
        assert info['host'] == host
        assert info['port'] == port


def test_connect_raises():
    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='ZMQ::127.0.0.1::{}'.format(PORT),
            properties={'timeout': 1},
        )
    )

    # no server running
    if sys.platform == 'win32':
        match = r'Timeout occurred after 1.0 second\(s\)'
    else:
        match = 'Connection refused'
    with pytest.raises(MSLConnectionError, match=match):
        record.connect()

    # start the ZMQ server
    p, filename = start_zmq_server()

    # invalid protocol
    record.connection.properties['protocol'] = 'invalid'
    with pytest.raises(MSLConnectionError, match='Protocol'):
        record.connect()

    # shut down the ZMQ server
    record.connection.properties.pop('protocol')
    dev = record.connect()
    dev.write('SHUTDOWN')
    dev.disconnect()
    dev.disconnect()  # can disconnect multiple times
    dev.disconnect()
    cleanup_zmq_server(p, filename)


def test_write_read():
    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='ZMQ::127.0.0.1::{}'.format(PORT),
            properties={'timeout': 1},
        )
    )

    # start the ZMQ server
    p, filename = start_zmq_server()

    dev = record.connect()
    assert dev.query('hello') == 'hello'
    assert dev.query('world', decode=False) == b'world'
    assert dev.query('123456789', size=4) == '1234'

    dev.timeout = 0.1
    with pytest.raises(MSLConnectionError):
        dev.query('sleep')

    dev.timeout = 1
    assert dev.read() == 'sleep'

    dev.disconnect()
    dev.reconnect()

    # shut down the ZMQ server
    dev.write('SHUTDOWN')
    dev.disconnect()
    cleanup_zmq_server(p, filename)


@pytest.mark.parametrize(
    ('socket_type', 'error_type'),
    [('invalid', AttributeError),
     ('MAXMSGSIZE', zmq.ZMQError)])
def test_bad_socket_type(socket_type, error_type):
    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='ZMQ::hostname::1234',
            properties={'socket_type': socket_type},
        )
    )

    with pytest.raises(error_type):
        record.connect()

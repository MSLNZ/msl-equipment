import socket
import threading

from msl.loadlib.utils import get_available_port

from msl.equipment import EquipmentRecord, ConnectionRecord
from msl.equipment.resources.omega import iTHX


def simulate_omega_iserver(address, port, term):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((address, port))
    s.listen(1)
    conn, _ = s.accept()

    while True:
        data = bytearray()
        while not data.endswith(term):
            data.extend(conn.recv(32))

        d = data.decode().rstrip()
        if d == 'SHUTDOWN':
            break
        elif d in ['*SRTC', '*SRTC2', '*SRTF', '*SRTF2']:
            # temperature
            conn.sendall(b'020.0' + term)
        elif d in ['*SRH', '*SRH2']:
            # humidity
            conn.sendall(b'040.0' + term)
        elif d in ['*SRD', '*SRDF', '*SRDC', '*SRDC2', '*SRDF', '*SRDF2']:
            # dewpoint
            conn.sendall(b'010.0' + term)
        elif d in ['*SRB', '*SRBF']:
            # temperature and humidity
            conn.sendall(b'020.0' + term + b',' + b'040.0' + term)
        else:
            conn.sendall(b'unhandled request' + term)
            break

    conn.close()
    s.close()


def test_omega_ithx_iserver():
    address = '127.0.0.1'
    port = get_available_port()
    term = b'\r'

    t = 20.0
    h = 40.0
    d = 10.0

    records = [
        EquipmentRecord(
            manufacturer='OMEGA',
            model='iTHX-W3',
            connection=ConnectionRecord(
                address='TCP::{}::{}'.format(address, port),
                backend='MSL',
                properties=dict(
                    termination=term,
                    timeout=2
                ),
            )
        ),

        # iTHX-W and iTHX-2 do not support the *SRB and *SRBF commands for
        # fetching both the temperature and humidity with a single write command
        EquipmentRecord(
            manufacturer='OMEGA',
            model='iTHX-2',
            connection=ConnectionRecord(
                address='TCP::{}::{}'.format(address, port),
                backend='MSL',
                properties=dict(
                    termination=term,
                    timeout=2
                ),
            )
        ),
    ]

    for index, record in enumerate(records):
        thread = threading.Thread(target=simulate_omega_iserver, args=(address, port, term))
        thread.daemon = True
        thread.start()

        dev = record.connect(demo=False)
        assert isinstance(dev, iTHX)

        assert dev.temperature() == t
        assert dev.temperature(probe=1) == t
        assert dev.temperature(probe=2) == t
        assert dev.temperature(probe=1, nbytes=6) == t
        assert dev.temperature(probe=2, nbytes=6) == t

        assert dev.humidity() == h
        assert dev.humidity(probe=1) == h
        assert dev.humidity(probe=2) == h
        assert dev.humidity(probe=1, nbytes=6) == h
        assert dev.humidity(probe=2, nbytes=6) == h

        assert dev.dewpoint() == d
        assert dev.dewpoint(probe=1) == d
        assert dev.dewpoint(probe=2) == d
        assert dev.dewpoint(probe=1, nbytes=6) == d
        assert dev.dewpoint(probe=2, nbytes=6) == d

        assert dev.temperature_humidity() == (t, h)
        assert dev.temperature_humidity(probe=1) == (t, h)
        assert dev.temperature_humidity(probe=2) == (t, h)
        assert dev.temperature_humidity(probe=1, nbytes=12) == (t, h)
        assert dev.temperature_humidity(probe=1, nbytes=13) == (t, h)
        assert dev.temperature_humidity(probe=2, nbytes=12) == (t, h)
        assert dev.temperature_humidity(probe=2, nbytes=13) == (t, h)

        assert dev.temperature_humidity_dewpoint() == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=1) == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=2) == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=1, nbytes=18) == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=1, nbytes=19) == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=1, nbytes=20) == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=2, nbytes=18) == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=2, nbytes=19) == (t, h, d)
        assert dev.temperature_humidity_dewpoint(probe=2, nbytes=20) == (t, h, d)

        dev.write('SHUTDOWN')
        dev.disconnect()
        thread.join()

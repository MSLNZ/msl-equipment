from __future__ import annotations

import os
import socket
import threading
import time
from datetime import datetime

from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord
from msl.equipment.resources.omega import iTHX


def simulate_omega_iserver(address, port, term):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((address, port))
    s.listen(10)
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


def test_temperature_humidity_dewpoint():
    address = '127.0.0.1'
    ports = [32153, 47209]
    term = b'\r'

    t = 20.0
    h = 40.0
    d = 10.0

    records = [
        EquipmentRecord(
            manufacturer='OMEGA',
            model='iTHX-W3',
            connection=ConnectionRecord(
                address='TCP::{}::{}'.format(address, ports[0]),
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
                address='TCP::{}::{}'.format(address, ports[1]),
                backend='MSL',
                properties=dict(
                    termination=term,
                    timeout=2
                ),
            )
        ),
    ]

    for index, record in enumerate(records):
        thread = threading.Thread(target=simulate_omega_iserver, args=(address, ports[index], term))
        thread.daemon = True
        thread.start()

        time.sleep(0.1)

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


def test_database():
    db_files = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir, 'db_files'))

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'), as_datetime=False)
    assert data == [
        (1, '2021-09-10T16:03:36', 19.5, 57.5, 10.8),
        (2, '2021-09-10T16:03:37', 19.5, 57.5, 10.8),
        (3, '2021-09-10T16:03:38', 19.5, 57.5, 10.8),
        (4, '2021-09-10T16:03:39', 19.5, 57.5, 10.8),
        (5, '2021-09-10T16:03:40', 19.5, 57.5, 10.8),
        (6, '2021-09-10T16:03:41', 19.5, 57.5, 10.8),
        (7, '2021-09-10T16:03:42', 19.5, 57.5, 10.8),
        (8, '2021-09-10T16:03:43', 19.5, 57.5, 10.8),
        (9, '2021-09-10T16:03:44', 19.5, 57.5, 10.8),
        (10, '2021-09-10T16:03:45', 19.5, 57.5, 10.8)
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-2probe.sqlite3'), as_datetime=False)
    assert data == [
        (1, '2021-09-10T16:01:52', 20.43, 56.23, 11.42, 19.28, 61.53, 11.7),
        (2, '2021-09-10T16:01:53', 20.43, 56.23, 11.41, 19.26, 61.55, 11.69),
        (3, '2021-09-10T16:01:54', 20.43, 56.23, 11.42, 19.28, 61.53, 11.69),
        (4, '2021-09-10T16:01:55', 20.43, 56.23, 11.42, 19.28, 61.53, 11.69),
        (5, '2021-09-10T16:01:56', 20.42, 56.23, 11.41, 19.27, 61.53, 11.69),
        (6, '2021-09-10T16:01:57', 20.43, 56.23, 11.42, 19.27, 61.53, 11.69),
        (7, '2021-09-10T16:01:58', 20.43, 56.23, 11.42, 19.28, 61.56, 11.71),
        (8, '2021-09-10T16:01:59', 20.43, 56.23, 11.42, 19.27, 61.53, 11.69),
        (9, '2021-09-10T16:02:00', 20.42, 56.23, 11.41, 19.27, 61.53, 11.69),
        (10, '2021-09-10T16:02:01', 20.42, 56.23, 11.41, 19.28, 61.53, 11.7)
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'), as_datetime=True)
    assert data[0] == (1, datetime(2021, 9, 10, 16, 3, 36), 19.5, 57.5, 10.8)

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'),
                     select='pid,temperature,dewpoint')
    assert data == [(i, 19.5, 10.8) for i in range(1, 11)]

    data = iTHX.data(os.path.join(db_files, 'iTHX-2probe.sqlite3'),
                     select=['temperature1', 'dewpoint2'])
    assert data == [
        (20.43, 11.7),
        (20.43, 11.69),
        (20.43, 11.69),
        (20.43, 11.69),
        (20.42, 11.69),
        (20.43, 11.69),
        (20.43, 11.71),
        (20.43, 11.69),
        (20.42, 11.69),
        (20.42, 11.7)
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'),
                     start='2021-09-10T16:03:39', as_datetime=False)
    assert data == [
        (4, '2021-09-10T16:03:39', 19.5, 57.5, 10.8),
        (5, '2021-09-10T16:03:40', 19.5, 57.5, 10.8),
        (6, '2021-09-10T16:03:41', 19.5, 57.5, 10.8),
        (7, '2021-09-10T16:03:42', 19.5, 57.5, 10.8),
        (8, '2021-09-10T16:03:43', 19.5, 57.5, 10.8),
        (9, '2021-09-10T16:03:44', 19.5, 57.5, 10.8),
        (10, '2021-09-10T16:03:45', 19.5, 57.5, 10.8)
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'),
                     start=datetime(2021, month=9, day=10, hour=16, minute=3, second=41), as_datetime=False)
    assert data == [
        (6, '2021-09-10T16:03:41', 19.5, 57.5, 10.8),
        (7, '2021-09-10T16:03:42', 19.5, 57.5, 10.8),
        (8, '2021-09-10T16:03:43', 19.5, 57.5, 10.8),
        (9, '2021-09-10T16:03:44', 19.5, 57.5, 10.8),
        (10, '2021-09-10T16:03:45', 19.5, 57.5, 10.8)
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'),
                     end='2021-09-10T16:03:38', as_datetime=False)
    assert data == [
        (1, '2021-09-10T16:03:36', 19.5, 57.5, 10.8),
        (2, '2021-09-10T16:03:37', 19.5, 57.5, 10.8),
        (3, '2021-09-10T16:03:38', 19.5, 57.5, 10.8),
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'),
                     end=datetime(2021, month=9, day=10, hour=16, minute=3, second=36), as_datetime=False)
    assert data == [
        (1, '2021-09-10T16:03:36', 19.5, 57.5, 10.8),
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'),
                     start='2021-09-10T16:03:39', end='2021-09-10T16:03:41', as_datetime=False)
    assert data == [
        (4, '2021-09-10T16:03:39', 19.5, 57.5, 10.8),
        (5, '2021-09-10T16:03:40', 19.5, 57.5, 10.8),
        (6, '2021-09-10T16:03:41', 19.5, 57.5, 10.8),
    ]

    data = iTHX.data(os.path.join(db_files, 'iTHX-1probe.sqlite3'),
                     start='2020-09-10', end='2020-01-01')
    assert data == []

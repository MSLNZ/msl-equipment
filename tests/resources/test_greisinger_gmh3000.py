import os
import threading
import time
try:
    import pty
except ImportError:
    pty = None

import pytest

from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord
from msl.equipment.exceptions import GreisingerError


def easybus_server(port):
    os.read(port, 3)  # value() request
    os.write(port, b'\xfe\x05&q\x00H\xf7\x80\t')  # 21.76
    os.read(port, 3)  # value() request
    os.write(port, b'\xFE\x05&\x72\xFF\x84\x00\xFC\x05')  # -0.04
    os.read(port, 6)  # min measurement range request
    os.write(port, b'\xfe\xf5\xf8O\x00g\xbf0\xe3')  # -200.0
    os.read(port, 6)  # max measurement range request
    os.write(port, b'\xfe\xf5\xf8N\x00r\x964\xec')  # 850.0
    os.read(port, 3)  # value() request
    os.write(port, b'\xfe\r\x1ep\xf6\x91\xdf\xed\x0b')  # "No sensor" error code


@pytest.mark.skipif(pty is None, reason='pty is not available')
def test_easybus():
    # simulate a Serial port
    primary, secondary = pty.openpty()

    thread = threading.Thread(target=easybus_server, args=(primary,), daemon=True)
    thread.start()

    time.sleep(0.5)  # allow some time for the easybus server to start

    record = EquipmentRecord(
        manufacturer='Greisinger',
        model='GMH3710-GE',
        connection=ConnectionRecord(
            address='ASRL' + os.ttyname(secondary),
            properties={'timeout': 5},
        )
    )

    dev = record.connect()
    assert dev.value() == 21.76
    assert dev.value() == -0.04
    assert dev.measurement_range() == (-200.0, 850.0)
    with pytest.raises(GreisingerError, match='No sensor'):
        dev.value()

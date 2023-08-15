import time
import math
import threading

import pytest
import pyvisa
from pyvisa.resources.tcpip import TCPIPSocket
from pyvisa.attributes import AttrVI_ATTR_TMO_VALUE

from msl.equipment.config import Config
from msl.equipment.connection_pyvisa import ConnectionPyVISA
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord

from test_connection_socket import echo_server_tcp, get_available_port

pyvisa_version = tuple(map(int, pyvisa.__version__.split('.')))
VISA_LIBRARY = '@ni' if pyvisa_version < (1, 11) else '@ivi'

try:
    pyvisa.ResourceManager(VISA_LIBRARY)
except:
    HAS_NI_VISA = False
else:
    HAS_NI_VISA = True


def teardown_module():
    import cleanup_os_environ
    cleanup_os_environ.cleanup()


@pytest.mark.skipif(not HAS_NI_VISA, reason='NI-VISA is not installed')
def test_resource_manager():
    assert isinstance(ConnectionPyVISA.resource_manager(), pyvisa.ResourceManager)
    assert isinstance(ConnectionPyVISA.resource_manager('@ni'), pyvisa.ResourceManager)
    assert isinstance(ConnectionPyVISA.resource_manager('@ivi'), pyvisa.ResourceManager)
    assert isinstance(ConnectionPyVISA.resource_manager('@py'), pyvisa.ResourceManager)


def test_resource_class():
    backends = (VISA_LIBRARY, '@py') if HAS_NI_VISA else ('@py',)

    for backend in backends:

        Config.PyVISA_LIBRARY = backend

        for item in ('ASRL1', 'ASRL1::INSTR', 'COM1', 'LPT1', 'ASRL::/dev/prt/1', 'ASRLCOM1'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.SerialInstrument

        for item in ('GPIB::2', 'GPIB::1::0::INSTR'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.GPIBInstrument

        for item in ('GPIB2::INTFC', ):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.GPIBInterface

        for item in ('PXI::15::INSTR', 'PXI::CHASSIS1::SLOT3', 'PXI0::2-12.1::INSTR'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.PXIInstrument

        for item in ('PXI0::MEMACC',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.PXIMemory

        for item in ('TCPIP::dev.company.com::INSTR',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.TCPIPInstrument

        for item in ('TCPIP0::1.2.3.4::999::SOCKET',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.TCPIPSocket

        for item in ('USB::0x1234::125::A22-5::INSTR',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.USBInstrument

        for item in ('USB::0x5678::0x33::SN999::1::RAW',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.USBRaw

        for item in ('VXI::1::BACKPLANE',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.VXIBackplane

        for item in ('VXI::MEMACC',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.VXIMemory

        for item in ('VXI0::1::INSTR', 'VXI0::SERVANT'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item, backend='PyVISA'))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.VXIInstrument

    with pytest.raises(ValueError):
        ConnectionPyVISA.resource_manager('@invalid')


def test_timeout_and_termination():
    Config.PyVISA_LIBRARY = '@py'

    address = '127.0.0.1'
    port = get_available_port()
    term = b'xyz'

    t = threading.Thread(target=echo_server_tcp, args=(address, port, term))
    t.daemon = True
    t.start()

    time.sleep(0.1)  # allow some time for the echo server to start

    record = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP::{}::{}::SOCKET'.format(address, port),
            backend='PyVISA',
            properties={'termination': term, 'timeout': 10}
        )
    )

    record2 = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP::{}::{}::SOCKET'.format(address, port),
            backend='PyVISA',
            properties={
                'write_termination': b'abc',
                'read_termination': '123',
                'timeout': 1000
            }
        )
    )

    record3 = EquipmentRecord(
        connection=ConnectionRecord(
            address='TCPIP::{}::{}::SOCKET'.format(address, port),
            backend='PyVISA',
        )
    )

    dev = record.connect()

    assert dev.timeout == 10000  # 10 seconds gets converted to 10000 ms
    assert dev.timeout == dev.resource.timeout
    assert dev.write_termination == term.decode()
    assert dev.write_termination == dev.resource.write_termination
    assert dev.read_termination == term.decode()
    assert dev.read_termination == dev.resource.read_termination

    dev2 = record2.connect()
    assert dev2.timeout == 1000  # >100 so does not get converted
    assert dev2.timeout == dev2.resource.timeout
    assert dev2.write_termination == 'abc'
    assert dev2.write_termination == dev2.resource.write_termination
    assert dev2.read_termination == '123'
    assert dev2.read_termination == dev2.resource.read_termination

    dev3 = record3.connect()
    assert dev3.timeout == AttrVI_ATTR_TMO_VALUE.default
    assert dev3.timeout == dev3.resource.timeout
    assert dev3.write_termination == TCPIPSocket._write_termination
    assert dev3.write_termination == dev3.resource.write_termination
    assert dev3.read_termination == TCPIPSocket._read_termination
    assert dev3.read_termination is None
    assert dev3.read_termination == dev3.resource.read_termination

    dev.timeout = 1234
    dev.write_termination = 'hello'
    dev.read_termination = 'goodbye'
    assert dev.timeout == 1234
    assert dev.timeout == dev.resource.timeout
    assert dev.write_termination == 'hello'
    assert dev.write_termination == dev.resource.write_termination
    assert dev.read_termination == 'goodbye'
    assert dev.read_termination == dev.resource.read_termination

    del dev.timeout
    dev.write_termination = None
    dev.read_termination = None
    assert math.isinf(dev.timeout)
    assert dev.timeout == dev.resource.timeout
    assert dev.write_termination is None
    assert dev.resource.write_termination is None
    assert dev.read_termination is None
    assert dev.resource.read_termination is None

    dev.timeout = 5000
    dev.write_termination = term.decode()
    dev.read_termination = term.decode()
    assert dev.timeout == 5000
    assert dev.timeout == dev.resource.timeout
    assert dev.write_termination == term.decode()
    assert dev.write_termination == dev.resource.write_termination
    assert dev.read_termination == term.decode()
    assert dev.read_termination == dev.resource.read_termination

    dev.timeout = None
    assert math.isinf(dev.timeout)
    assert dev.timeout == dev.resource.timeout

    assert dev.query('*IDN?') == '*IDN?'

    dev.write('SHUTDOWN')
    dev.disconnect()
    dev2.disconnect()
    dev3.disconnect()

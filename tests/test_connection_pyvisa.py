import pyvisa

from msl.equipment.config import Config
from msl.equipment.connection_pyvisa import ConnectionPyVISA
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord


def test_resource_manager():
    assert isinstance(ConnectionPyVISA.resource_manager(), pyvisa.ResourceManager)


def test_pyclass():

    for backend in ('@ni', '@py'):

        Config.PyVISA_LIBRARY = backend

        for item in ('ASRL::1.2.3.4::2::INSTR', 'ASRL1::INSTR', 'COM1', 'LPT1'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.SerialInstrument

        for item in ('GPIB::2', 'GPIB::1::0::INSTR'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.GPIBInstrument

        for item in ('GPIB2::INTFC', ):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.GPIBInterface

        for item in ('PXI::15::INSTR', 'PXI::CHASSIS1::SLOT3', 'PXI0::2-12.1::INSTR'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.PXIInstrument

        for item in ('PXI0::MEMACC',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.PXIMemory

        for item in ('TCPIP::dev.company.com::INSTR',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.TCPIPInstrument

        for item in ('TCPIP0::1.2.3.4::999::SOCKET',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.TCPIPSocket

        for item in ('USB::0x1234::125::A22-5::INSTR',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.USBInstrument

        for item in ('USB::0x5678::0x33::SN999::1::RAW',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.USBRaw

        for item in ('VXI::1::BACKPLANE',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.VXIBackplane

        for item in ('VXI::MEMACC',):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.VXIMemory

        for item in ('VXI0::1::INSTR', 'VXI0::SERVANT'):
            record = EquipmentRecord(connection=ConnectionRecord(address=item))
            assert ConnectionPyVISA.resource_class(record) == pyvisa.resources.VXIInstrument

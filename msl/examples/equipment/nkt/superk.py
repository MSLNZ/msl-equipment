"""
Example showing how to communicate with a SuperK Fianium laser using the NKT SDK.
"""
import time

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.exceptions import NKTError

record = EquipmentRecord(
    manufacturer='NKT',
    model='SuperK Fianium',  # change for your device
    connection=ConnectionRecord(
        address='COM6',  # change for your computer
        backend=Backend.MSL,
        # When installing the SDK a NKTP_SDK_PATH environment variable is created
        # and this variable is used to specify the path to the dll file. However, you
        # can also explicitly specify the location of the dll file.
        properties={'sdk_path': r'D:\NKTPDLL.dll'},
    )
)

# Device ID of the SuperK Fianium mainboard
DEVICE_ID = 15

# Connect to the SuperK laser
nkt = record.connect()

# Get some info about the SuperK
print('The status of the SuperK: {!r}'.format(nkt.get_port_status()))
print('The following modules are available in the device:')
for module, DEVICE_ID in nkt.get_modules().items():
    print('  ModuleType={} DeviceID={}'.format(module, DEVICE_ID))
    print('    Status bits: {}'.format(nkt.device_get_status_bits(DEVICE_ID)))
    print('    Type: 0x{:04x}'.format(nkt.device_get_type(DEVICE_ID)))
    print('    Firmware Version#: {}'.format(nkt.device_get_firmware_version_str(DEVICE_ID)))
    print('    Serial#: {}'.format(nkt.device_get_module_serial_number_str(DEVICE_ID)))
    try:
        print('    PCB Serial#: {}'.format(nkt.device_get_pcb_serial_number_str(DEVICE_ID)))
    except NKTError:
        print('    PCB Serial#: Not Available')
    try:
        print('    PCB Version#: {}'.format(nkt.device_get_pcb_version(DEVICE_ID)))
    except NKTError:
        print('    PCB Version#: Not Available')
    print('    Is Live?: {}'.format(nkt.device_get_live(DEVICE_ID)))

# Check the Interlock status
ilock = nkt.register_read_u16(DEVICE_ID, 0x32)
print('Interlock OK? {}'.format(ilock == 2))
if ilock == 1:  # then requires an interlock reset
    nkt.register_write_u16(DEVICE_ID, 0x32, 1)  # reset interlock
    print('Interlock OK? {}'.format(nkt.register_read_u16(DEVICE_ID, 0x32) == 2))

# The documentation indicates that there is a scaling factor of 0.1
print('Temperature: {:.2f} deg C'.format(nkt.register_read_u16(DEVICE_ID, 0x11) * 0.1))
print('Level {}%'.format(nkt.register_read_u16(DEVICE_ID, 0x37) * 0.1))

# Set the operating mode and get the operating mode in a single function call
print('Operating mode: {}'.format(nkt.register_write_read_u16(DEVICE_ID, 0x31, 1)))

# Set the output level to 5.5% (the docs of the DLL indicate that there is a 0.1 scaling factor)
print('Set level to 5.5%')
nkt.register_write_u16(DEVICE_ID, 0x37, 55)

# Get the output level
print('Level {}%'.format(nkt.register_read_u16(DEVICE_ID, 0x37) * 0.1))

# Turn on the laser
print('Turn laser on')
nkt.register_write_u8(DEVICE_ID, 0x30, 3)

print('Sleep for 5 seconds')
time.sleep(5)

# Turn off the laser
print('Turn laser off')
nkt.register_write_u8(DEVICE_ID, 0x30, 0)

# Disconnect from the laser
nkt.disconnect()

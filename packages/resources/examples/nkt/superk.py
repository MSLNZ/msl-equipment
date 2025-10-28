"""Example showing how to communicate with a SuperK Fianium laser using the NKT SDK."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection, MSLConnectionError

if TYPE_CHECKING:
    from msl.equipment.resources import NKT


connection = Connection(
    "COM6",  # update for your device
    manufacturer="NKT",
    model="SuperK Fianium",  # update for your device
    sdk_path="C:/NKT/NKTPDLL.dll",  # path to the NKT SDK
)

# Device ID of the SuperK Fianium mainboard
DEVICE_ID = 15

INTERLOCK_OK = 2

# Connect to the SuperK laser
nkt: NKT = connection.connect()

# Get some info about the SuperK
print(f"The status of the SuperK: {nkt.get_port_status()!r}")
print("The following modules are available in the device:")
for module, device_id in nkt.get_modules().items():
    print(f"  ModuleType={module} DeviceID={device_id}")
    print(f"    Status bits: {nkt.device_get_status_bits(device_id)}")
    print(f"    Type: 0x{nkt.device_get_type(device_id):04x}")
    print(f"    Firmware Version#: {nkt.device_get_firmware_version_str(device_id)}")
    print(f"    Serial#: {nkt.device_get_module_serial_number_str(device_id)}")
    try:
        print(f"    PCB Serial#: {nkt.device_get_pcb_serial_number_str(device_id)}")
    except MSLConnectionError:
        print("    PCB Serial#: Not Available")
    try:
        print(f"    PCB Version#: {nkt.device_get_pcb_version(device_id)}")
    except MSLConnectionError:
        print("    PCB Version#: Not Available")
    print(f"    Is Live?: {nkt.device_get_live(device_id)}")

# Check the Interlock status
interlock = nkt.register_read_u16(DEVICE_ID, 0x32)
print(f"Interlock OK? {interlock == INTERLOCK_OK}")
if interlock == 1:  # then requires an interlock reset
    nkt.register_write_u16(DEVICE_ID, 0x32, 1)  # reset interlock
    print(f"Interlock OK? {nkt.register_read_u16(DEVICE_ID, 0x32) == INTERLOCK_OK}")

# The documentation indicates that there is a scaling factor of 0.1
print(f"Temperature: {nkt.register_read_u16(DEVICE_ID, 0x11) * 0.1:.2f} deg C")
print(f"Level {nkt.register_read_u16(DEVICE_ID, 0x37) * 0.1}%")

# Set the operating mode and get the operating mode in a single function call
print(f"Operating mode: {nkt.register_write_read_u16(DEVICE_ID, 0x31, 1)}")

# Set the output level to 5.5% (the docs of the DLL indicate that there is a 0.1 scaling factor)
print("Set level to 5.5%")
nkt.register_write_u16(DEVICE_ID, 0x37, 55)

# Get the output level
print(f"Level {nkt.register_read_u16(DEVICE_ID, 0x37) * 0.1}%")

# Turn on the laser
print("Turn laser on")
nkt.register_write_u8(DEVICE_ID, 0x30, 3)

print("Sleep for 5 seconds")
time.sleep(5)

# Turn off the laser
print("Turn laser off")
nkt.register_write_u8(DEVICE_ID, 0x30, 0)

# Disconnect from the laser
nkt.disconnect()

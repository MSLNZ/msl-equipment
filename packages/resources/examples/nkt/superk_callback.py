"""Example showing how to use callbacks with a SuperK Fianium laser.

This example requires the NKTPDLL.dll library.
"""

from __future__ import annotations

from ctypes import c_ubyte

from msl.equipment import Connection
from msl.equipment.resources import NKTDLL, nkt


@nkt.register_status_callback
def register_callback(
    port: str,
    dev_id: int,
    reg_id: int,
    reg_status: int,
    reg_type: int,
    length: int,
    address: int,
) -> None:
    """A register-status callback handler."""
    # 'address' is an integer and represents the address of c_void_p from the callback
    data = bytes((c_ubyte * length).from_address(address)[:])
    status = nkt.RegisterStatus(reg_status)
    dtype = nkt.RegisterData(reg_type)
    print(f"RegisterStatusCallback: {port}, {dev_id}, {reg_id}, {status!r}, {dtype!r}, {data!r}")


@nkt.port_status_callback
def port_callback(port: str, status: int, cur_scan: int, max_scan: int, device: int) -> None:
    """A port-status callback handler."""
    print(f"PortStatusCallback: {port}, {nkt.PortStatus(status)!r}, {cur_scan}, {max_scan}, {device}")


@nkt.device_status_callback
def device_callback(port: str, dev_id: int, status: int, length: int, address: int) -> None:
    """A device-status callback handler."""
    # 'address' is an integer and represents the address of c_void_p from the callback
    data = bytes((c_ubyte * length).from_address(address)[:])
    print(f"DeviceStatusCallback: {port}, {dev_id}, {nkt.DeviceStatus(status)!r}, {data!r}")


# Load the SDK before before connecting to the laser just to see the PortStatusCallback
# messages for this example.
#
# When installing the SDK a NKTP_SDK_PATH environment variable is created
# and this variable specifies the path to the DLL file; however, you
# can also explicitly specify the path to the DLL file.
NKTDLL.load_sdk(r"C:\NKT Photonics\SDK\NKTPDLL\x64\NKTPDLL.dll")
NKTDLL.set_callback_port_status(port_callback)


connection = Connection(
    "COM4",  # update for your device
    manufacturer="NKT",
    model="NKTDLL",  # must be "NKTDLL"
)

# Device ID of the SuperK Fianium mainboard
DEVICE_ID = 15

INTERLOCK_OK = 2

# Connect to the laser
laser: NKTDLL = connection.connect()

# set the register and device callback function handlers
laser.set_callback_register_status(register_callback)
laser.set_callback_device_status(device_callback)

# Check the Interlock status
interlock = laser.register_read_u16(DEVICE_ID, 0x32)
print(f"Interlock OK? {interlock == INTERLOCK_OK}")
if interlock == 1:  # then requires an interlock reset
    laser.register_write_u16(DEVICE_ID, 0x32, 1)  # reset interlock
    print(f"Interlock OK? {laser.register_read_u16(DEVICE_ID, 0x32) == INTERLOCK_OK}")

# The documentation indicates that there is a scaling factor of 0.1
print(f"Temperature: {laser.register_read_u16(DEVICE_ID, 0x11) * 0.1} deg C")
print(f"Level {laser.register_read_u16(DEVICE_ID, 0x37) * 0.1}%")

# Set to Power mode and get the Power mode in a single function call
print(f"Is in Power mode? {bool(laser.register_write_read_u16(DEVICE_ID, 0x31, 1))}")

# Set the power level to 5.5% (the docs of the DLL indicate that there is a 0.1 scaling factor)
print("Set level to 5.5%")
laser.register_write_u16(DEVICE_ID, 0x37, 55)

# Get the power level
print(f"Level {laser.register_read_u16(DEVICE_ID, 0x37) * 0.1} %")

# Disconnect from the laser
laser.disconnect()

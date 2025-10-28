"""Example showing how to find all devices from NKT Photonics."""

from __future__ import annotations

from msl.equipment.resources import NKT

# When installing the SDK a NKTP_SDK_PATH environment variable is created
# and this variable specifies the path to the DLL file; however, you
# can also explicitly specify the path to the DLL file.
NKT.load_sdk("C:/NKTPDLL.dll")

print("Finding all available ports...")
all_ports = NKT.get_all_ports()
print(f"  Found the following ports: {all_ports}")

# Open all ports (in Auto and Live modes)
print("Opening all ports (in Auto and Live modes)...")
NKT.open_ports(*all_ports)

# All ports returned by the get_open_ports() function have modules
# (ports without modules will be closed automatically)
opened_ports = NKT.get_open_ports()
print(f"  Devices from NKT Photonics are open on the following ports: {opened_ports}")

# Traverse the opened_ports list and retrieve information about the device types and the addresses
# See the Register Files section in the SDK manual
all_types = NKT.device_get_all_types(*opened_ports)
for name, types in all_types.items():
    print(f"  Port: {name}")
    for module, device_id in types.items():
        print(f"    ModuleType={module} DeviceID={device_id}")

# Close all ports
NKT.close_ports()
print("Closed all ports")

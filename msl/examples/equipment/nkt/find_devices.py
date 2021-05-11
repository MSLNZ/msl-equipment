"""
Example showing how to find all devices from NKT Photonics.
"""
from msl.equipment.resources import NKT

# When installing the SDK a NKTP_SDK_PATH environment variable is created
# and this variable specifies the path of the dll file. However, you
# can also explicitly specify the path of the dll file. For example, you
# can use NKT.load_sdk() to automatically find the DLL file.
NKT.load_sdk(path='D:/NKTPDLL.dll')

print('Finding all available ports...')
all_ports = NKT.get_all_ports()
print('  Found the following ports: {}'.format(all_ports))

# Open all ports (in Auto and Live modes)
print('Opening all ports (in Auto and Live modes)...')
NKT.open_ports(all_ports)

# All ports returned by the get_open_ports() function have modules
# (ports without modules will be closed automatically)
opened_ports = NKT.get_open_ports()
print('  Devices from NKT Photonics are open on the following ports: {}'.format(opened_ports))

# Traverse the opened_ports list and retrieve information about the device types and the addresses
# See the Register Files section in the SDK manual
types = NKT.device_get_all_types(opened_ports)
for name, types in types.items():
    print('  Port: ' + name)
    for module, device_id in types.items():
        print('    ModuleType={} DeviceID={}'.format(module, device_id))

# Close all ports
NKT.close_ports()
print('Closed all ports')

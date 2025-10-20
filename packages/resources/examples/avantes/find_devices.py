"""Example showing how to find all AvaSpec devices that are available.

The AvaSpec shared library may require a Visual C++ Redistributable Package to be installed (on Windows).
"""

import os

from msl.equipment.resources import AvaSpec

# You can either specify the full path to the SDK
# (e.g., C:/AvaSpecX64-DLL_9.7/avaspecx64.dll) in the Avantes.find()
# function, or, you can add the directory where the avaspecx64 library file is located
# to your PATH environment variable
os.environ["PATH"] += os.pathsep + r"C:\AvaSpecX64-DLL_9.7"

devices = AvaSpec.find()
if devices:
    print("Found the following Avantes devices: ")
    for device in devices:
        print(f"  SerialNumber: {device.SerialNumber}")
        print(f"  UserFriendlyName: {device.UserFriendlyName}")
        print(f"  Status: {device.Status}")
else:
    print("Could not find any AvaSpec devices")

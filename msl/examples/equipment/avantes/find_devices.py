"""
Example showing how to find all Avantes devices that are available.
"""
import sys

from msl.equipment.resources import Avantes

# You can either specify the full path to the SDK
# (e.g., D:/AvaSpecX64-DLL_9.7/avaspecx64.dll) in the Avantes.find()
# function, or, you can add the directory where the DLL file is
# located to sys.path
sys.path.append(r'D:\AvaSpecX64-DLL_9.7')

found = Avantes.find()
if found:
    print('Found the following Avantes devices: ')
    for device in found:
        print('  SerialNumber: {}'.format(device.SerialNumber))
        print('  UserFriendlyName: {}'.format(device.UserFriendlyName))
        print('  Status: {}'.format(device.Status))
else:
    print('Could not find any Avantes devices')

"""
Example showing how to find all Avantes devices that are available.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import sys

    from msl.equipment.resources.avantes import get_list

    # You can either specify the full path to the SDK (including the filename
    # e.g., D:/AvaSpecX64-DLL_9.7/avaspecx64.dll) in the get_list() function, or,
    # you can specify the root directory where the .dll file is located in `sys.path`
    sys.path.append('D:/AvaSpecX64-DLL_9.7')

    print('Found the following Avantes devices: ')
    for device in get_list():
        print('  SerialNumber: {}'.format(device.SerialNumber))
        print('  UserFriendlyName: {}'.format(device.UserFriendlyName))
        print('  Status: {}'.format(device.Status))

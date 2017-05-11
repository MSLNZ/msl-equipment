"""
This example shows how to get information about devices found on USB ports, 
that are not currently ``open()`` using the Thorlabs Kinesis SDK.
"""

# this if statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import sys

    from msl.equipment.resources.thorlabs import MotionControl

    print('Building the device list...')
    MotionControl.build_device_list()

    n_devices = MotionControl.get_device_list_size()
    if n_devices == 0:
        print('There are no devices in the device list')
        sys.exit(0)
    elif n_devices == 1:
        print('There is 1 device in the device list')
    else:
        print('There are {} devices in the device list'.format(n_devices))

    all_devices = MotionControl.get_device_list()
    print('The serial numbers of all the devices are: {}'.format(all_devices))

    filter_flippers = MotionControl.get_device_list(MotionControl.Filter_Flipper)
    print('The Filter Flipper\'s that are connected are: {}'.format(filter_flippers))

    lts = MotionControl.get_device_list(MotionControl.Long_Travel_Stage)
    print('The Long Travel Stage\'s that are connected are: {}'.format(lts))

    devices = MotionControl.get_device_list(MotionControl.Filter_Flipper, MotionControl.Long_Travel_Stage)
    print('The Filter Flipper\'s and Long Travel Stage\'s that are connected are: {}'.format(devices))

    info = MotionControl.get_device_info(all_devices[0])
    print('The device info for the device with serial# {} is:'.format(all_devices[0]))
    for item in dir(info):
        if item.startswith('_'):
            continue
        print('\t{}: {}'.format(item, getattr(info, item)))

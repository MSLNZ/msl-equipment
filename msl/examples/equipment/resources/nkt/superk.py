"""
Example showing how to communicate with a SuperK Fianium laser using the NKT SDK.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    record = EquipmentRecord(
        manufacturer='NKT',
        model='SuperK Fianium',  # change for your device
        connection=ConnectionRecord(
            address='COM9',  # change for your device
            backend=Backend.MSL,
            # When installing the SDK a NKTP_SDK_PATH environment variable is created
            # and this variable is used to specify the path to the dll file. However, you
            # can also explicitly specify the location of the dll file.
            properties={'dll_path': r'D:\SDKs\NKTPDLL.dll'},
        )
    )

    # Connect to the laser
    nkt = record.connect()

    # Get some info about The SuperK
    print('The status of the SuperK: {!r}'.format(nkt.get_port_status()))
    print('The following modules are available in the device:')
    for module, device_id in nkt.get_modules().items():
        print('  ModuleType={} DeviceID={}'.format(module, device_id))
        print('    Status bits: {}'.format(nkt.device_get_status_bits(device_id)))
        print('    Type: {}'.format(nkt.device_get_type(device_id)))
        print('    Firmware Version#: {}'.format(nkt.device_get_firmware_version_str(device_id)))
        print('    Serial#: {}'.format(nkt.device_get_module_serial_number_str(device_id)))
        print('    PCB Serial#: {}'.format(nkt.device_get_pcb_serial_number_str(device_id)))
        print('    PCB Version#: {}'.format(nkt.device_get_pcb_version(device_id)))
        print('    Is Live?: {}'.format(nkt.device_get_live(device_id)))

    device_id = 15

    # Check the Interlock status
    ilock = nkt.register_read_u16(device_id, 0x32)
    print('Interlock OK? {}'.format(ilock == 2))
    if ilock == 1:  # then requires an interlock reset
        nkt.register_write_u16(device_id, 0x32, 1)  # reset interlock
        print('Interlock OK? {}'.format(nkt.register_read_u16(device_id, 0x32) == 2))

    # The documentation indicates that there is a scaling factor of 0.1
    print('Temperature: {} deg C'.format(nkt.register_read_u16(device_id, 0x11) * 0.1))
    print('Power level {}%'.format(nkt.register_read_u16(device_id, 0x37) * 0.1))
    print('Current level {}%'.format(nkt.register_read_u16(device_id, 0x38) * 0.1))

    # Set to Power mode and get the Power mode in a single function call
    print('Is in Power mode? {}'.format(bool(nkt.register_write_read_u16(device_id, 0x31, 1))))

    # Set the power to 5.5% (the 0.1 scaling factor means that we must multiply the value by 10)
    nkt.register_write_u16(device_id, 0x37, 55)
    # Get the current power value
    print('Power level {}%'.format(nkt.register_read_u16(device_id, 0x37) * 0.1))

    # Turn on the laser
    nkt.register_write_u8(device_id, 0x30, 3)

    time.sleep(5)

    # Turn off the laser
    nkt.register_write_u8(device_id, 0x30, 0)

    # Disconnect from the laser
    nkt.disconnect()

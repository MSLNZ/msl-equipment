"""
Example showing how to use callbacks with a SuperK Fianium laser.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    from msl.equipment.resources.nkt import NKT, RegisterStatusCallback, PortStatusCallback, DeviceStatusCallback
    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    @RegisterStatusCallback
    def register_callback(port, dev_id, reg_id, reg_status, reg_type, data_length, data):
        print('RegisterStatusCallback: {}'.format((port, dev_id, reg_id, reg_status, reg_type, data_length, data)))

    @PortStatusCallback
    def port_callback(port, status, address, total, device):
        print('PortStatusCallback: {}'.format((port, status, address, total, device)))

    @DeviceStatusCallback
    def device_callback(port, dev_id, status, data_length, data):
        print('DeviceStatusCallback: {}'.format((port, dev_id, status, data_length, data)))

    # Load the SDK before before connecting to the laser just to see the PortStatusCallback messages.
    # When installing the SDK a NKTP_SDK_PATH environment variable is created
    # and this variable specifies the path of the dll file. However, you
    # can also explicitly specify the path of the dll file. For example, you
    # can use NKT.load_sdk() to automatically find the DLL file.
    NKT.load_sdk('D:/NKTPDLL.dll')
    NKT.set_callback_port_status(port_callback)

    record = EquipmentRecord(
        manufacturer='NKT',
        model='SuperK Fianium',  # change for your device
        connection=ConnectionRecord(
            address='COM9',  # change for your computer
            backend=Backend.MSL,
        )
    )

    # Connect to the laser
    nkt = record.connect()

    # You can also use the "nkt" object to set the callbacks
    nkt.set_callback_register_status(register_callback)
    nkt.set_callback_device_status(device_callback)

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

    # Disconnect from the laser
    nkt.disconnect()

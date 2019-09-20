"""
Example showing how to use callbacks with a SuperK Fianium laser.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    from ctypes import c_ubyte

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend
    from msl.equipment.resources.nkt import NKT

    @NKT.RegisterStatusCallback
    def register_callback(port, dev_id, reg_id, reg_status, reg_type, length, address):
        # 'address' is an integer and represents the address of c_void_p from the callback
        data = bytearray((c_ubyte * length).from_address(address)[:])
        status = NKT.RegisterStatusTypes(reg_status)
        dtype = NKT.RegisterDataTypes(reg_type)
        print('RegisterStatusCallback: {}'.format((port, dev_id, reg_id, status, dtype, data)))

    @NKT.PortStatusCallback
    def port_callback(port, status, cur_scan, max_scan, device):
        print('PortStatusCallback: {}'.format((port, NKT.PortStatusTypes(status), cur_scan, max_scan, device)))

    @NKT.DeviceStatusCallback
    def device_callback(port, dev_id, status, length, address):
        # 'address' is an integer and represents the address of c_void_p from the callback
        data = bytearray((c_ubyte * length).from_address(address)[:])
        print('DeviceStatusCallback: {}'.format((port, dev_id, NKT.DeviceStatusTypes(status), data)))

    # Load the SDK before before connecting to the laser just to see the PortStatusCallback messages.
    # When installing the SDK a NKTP_SDK_PATH environment variable is created
    # and this variable specifies the path of the dll file. However, you
    # can also explicitly specify the path of the dll file. For example, you
    # can use NKT.load_sdk() to automatically find the DLL file.
    NKT.load_sdk(r'D:\NKTPDLL.dll')
    NKT.set_callback_port_status(port_callback)

    record = EquipmentRecord(
        manufacturer='NKT',
        model='SuperK Fianium',  # change for your device
        connection=ConnectionRecord(
            address='COM6',  # change for your computer
            backend=Backend.MSL,
        )
    )

    DEVICE_ID = 15

    # Connect to the laser
    nkt = record.connect()

    # You can also use the "nkt" object to set the callbacks
    nkt.set_callback_register_status(register_callback)
    nkt.set_callback_device_status(device_callback)

    # Check the Interlock status
    ilock = nkt.register_read_u16(DEVICE_ID, 0x32)
    print('Interlock OK? {}'.format(ilock == 2))
    if ilock == 1:  # then requires an interlock reset
        nkt.register_write_u16(DEVICE_ID, 0x32, 1)  # reset interlock
        print('Interlock OK? {}'.format(nkt.register_read_u16(DEVICE_ID, 0x32) == 2))

    # The documentation indicates that there is a scaling factor of 0.1
    print('Temperature: {} deg C'.format(nkt.register_read_u16(DEVICE_ID, 0x11) * 0.1))
    print('Power level {}%'.format(nkt.register_read_u16(DEVICE_ID, 0x37) * 0.1))
    print('Current level {}%'.format(nkt.register_read_u16(DEVICE_ID, 0x38) * 0.1))

    # Set to Power mode and get the Power mode in a single function call
    print('Is in Power mode? {}'.format(bool(nkt.register_write_read_u16(DEVICE_ID, 0x31, 1))))

    # Set the power level to 5.5% (the docs of the DLL indicate that there is a 0.1 scaling factor)
    nkt.register_write_u16(DEVICE_ID, 0x37, 55)

    # Get the power level
    print('Power level {} %'.format(nkt.register_read_u16(DEVICE_ID, 0x37) * 0.1))

    # Disconnect from the laser
    nkt.disconnect()

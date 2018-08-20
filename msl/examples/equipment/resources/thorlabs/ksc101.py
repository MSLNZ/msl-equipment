"""
This example shows how to communicate with a SH05 (shutter) connected to a KSC101 (KCube Solenoid).
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    # ensure that the Kinesis folder is available on PATH
    os.environ['PATH'] += os.pathsep + 'C:/Program Files/Thorlabs/Kinesis'

    # rather than reading the EquipmentRecord from a database we can create it manually
    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='KSC101',
        serial='68000297',  # update the serial number for your KSC101
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::Thorlabs.MotionControl.KCube.Solenoid.dll',
        ),
    )

    def is_open():
        return shutter.get_operating_state() == 1

    # connect to the KCube Solenoid
    shutter = record.connect()
    print('Connected to {}'.format(shutter))

    # start polling at 200 ms
    shutter.start_polling(200)

    # set the operating mode to SC_OperatingModes.SC_Manual
    shutter.set_operating_mode('Manual')

    for i in range(5):

        # set the operating state to SC_OperatingStates.SC_Active
        print('Opening the shutter...')
        shutter.set_operating_state('Active')
        while not is_open():
            time.sleep(0.05)
        print('  Is the shutter open? {}'.format(is_open()))

        time.sleep(1)

        # set the operating state to SC_OperatingStates.SC_Inactive
        print('Closing the shutter...')
        shutter.set_operating_state('Inactive')
        while is_open():
            time.sleep(0.05)
        print('  Is the shutter open? {}'.format(is_open()))

        time.sleep(1)

    # stop polling and close the connection
    shutter.stop_polling()
    shutter.disconnect()

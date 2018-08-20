"""
This example shows how to communicate with Thorlabs KST101, KCube Stepper Motor.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    from pprint import pprint

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    # ensure that the Kinesis folder is available on PATH
    os.environ['PATH'] += os.pathsep + 'C:/Program Files/Thorlabs/Kinesis'

    # rather than reading the EquipmentRecord from a database we can create it manually
    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='KST101',
        serial='26000908',  # update the serial number for your KST101
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::Thorlabs.MotionControl.KCube.StepperMotor.dll',
        ),
    )

    def wait(value):
        motor.clear_message_queue()
        message_type, message_id, _ = motor.wait_for_message()
        while message_type != 2 or message_id != value:
            position = motor.get_position()
            real = motor.get_real_value_from_device_unit(position, 'DISTANCE')
            print('  at position {} [device units] {} [real-world units]'.format(position, real))
            message_type, message_id, _ = motor.wait_for_message()

    # connect to the KCube Stepper Motor
    motor = record.connect()
    print('Connected to {}'.format(motor))

    # load the configuration settings (so that we can use the get_real_value_from_device_unit() method)
    motor.load_settings()

    # start polling at 200 ms
    motor.start_polling(200)

    # home the device
    print('Homing...')
    motor.home()
    wait(0)
    print('Homing done. At position {} [device units]'.format(motor.get_position()))

    # move to position 100000
    print('Moving to 100000...')
    motor.move_to_position(100000)
    wait(1)
    print('Moving done. At position {} [device units]'.format(motor.get_position()))

    # move by a relative amount of -5000
    print('Moving by -5000...')
    motor.move_relative(-5000)
    wait(1)
    print('Moving done. At position {} [device units]'.format(motor.get_position()))

    # jog forwards
    print('Jogging forwards by {} [device units]'.format(motor.get_jog_step_size()))
    motor.move_jog('Forwards')
    wait(1)
    print('Jogging done. At position {} [device units]'.format(motor.get_position()))

    # stop polling and close the connection
    motor.stop_polling()
    motor.disconnect()

    # you can access the default settings for the motor to pass to the set_*() methods
    print('\nThe default motor settings are:')
    pprint(motor.settings)

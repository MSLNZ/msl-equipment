"""
This example shows how to communicate with Thorlabs KDC101, KCube DC Servo.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend
    from msl.equipment.resources.thorlabs.kinesis.enums import UnitType

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    # you must update the following values
    kinesis_path = 'C:/Program Files/Thorlabs/Kinesis'
    serial_number = '27251265'

    # the Thorlabs.MotionControl.KCube.DCServo.dll depends on other DLLs from Thorlabs
    # make sure to add the Kinesis folder to the environment PATH
    os.environ['PATH'] += os.pathsep + kinesis_path

    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='KDC101',
        serial=serial_number,
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::KCubeDCServo::Thorlabs.MotionControl.KCube.DCServo.dll',
        ),
    )

    motor = record.connect()
    print(motor)

    # start the device polling at 200-ms intervals
    motor.start_polling(200)

    info = motor.get_hardware_info()
    print('Found device: {}'.format(info.notes))

    motor_params = motor.get_motor_params_ext()
    print('Motor Parameters : {}, {}, {}'.format(*motor_params))

    vmax, acc = motor.get_vel_params()
    vmax_real = motor.get_real_value_from_device_unit(vmax, UnitType.VELOCITY)
    acc_real = motor.get_real_value_from_device_unit(acc, UnitType.ACCELERATION)
    print('Max Velocity [device units]= {}'.format(vmax))
    print('Max Velocity [real-world units]= {} mm/s'.format(vmax_real))
    print('Acceleration [device units]= {}'.format(acc))
    print('Acceleration [real-world units]= {} mm/s^2'.format(acc_real))

    pos = motor.get_position()
    print('Current position [device units]= {}'.format(pos))
    print('Current position [mm]= {}'.format(motor.get_real_value_from_device_unit(pos, UnitType.DISTANCE)))

    # home the device and wait for the move to finish
    motor.home()
    while motor.get_position() != 0:
        time.sleep(motor.polling_duration()*1e-3)
        print('Going home... at position index {}'.format(motor.get_position()))

    time.sleep(1)

    # move to 5 mm and wait for the move to finish
    new_position = motor.get_device_unit_from_real_value(5.0, UnitType.DISTANCE)
    motor.move_to_position(new_position)
    while motor.get_position() != new_position:
        time.sleep(motor.polling_duration()*1e-3)
        print('Move to 5 mm [device units={}]... at position index {}'.format(new_position, motor.get_position()))

    pos = motor.get_position()
    print('Position [device units]= {}'.format(pos))
    print('Position [real-world units]= {}'.format(motor.get_real_value_from_device_unit(pos, UnitType.DISTANCE)))

    # close the connection
    motor.stop_polling()
    motor.close()

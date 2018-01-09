"""
This example shows how to communicate with Thorlabs LTS150, 150-mm Translation Stage with Stepper Motor.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend
    from msl.equipment.resources.thorlabs.kinesis.enums import UnitType

    # you must update the following values
    kinesis_path = 'C:/Program Files/Thorlabs/Kinesis'
    serial_number = '45870601'

    # the Thorlabs.MotionControl.IntegratedStepperMotors.dll depends on other DLLs from Thorlabs
    # make sure to add the Kinesis folder to the environment PATH
    os.environ['PATH'] += os.pathsep + kinesis_path

    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='LTS150/M',
        serial=serial_number,
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::IntegratedStepperMotors::Thorlabs.MotionControl.IntegratedStepperMotors.dll',
        ),
    )

    stage = record.connect()
    print(stage)

    # start the device polling at 200-ms intervals
    stage.start_polling(200)

    info = stage.get_hardware_info()
    print('Found device: {}'.format(info.notes))

    vmax, acc = stage.get_vel_params()
    vmax_real = stage.get_real_value_from_device_unit(vmax, UnitType.VELOCITY)
    acc_real = stage.get_real_value_from_device_unit(acc, UnitType.ACCELERATION)
    print('Max Velocity [device units]= {}'.format(vmax))
    print('Max Velocity [real-world units]= {} mm/s'.format(vmax_real))
    print('Acceleration [device units]= {}'.format(acc))
    print('Acceleration [real-world units]= {} mm/s^2'.format(acc_real))

    pos = stage.get_position()
    print('Current position [device units]= {}'.format(pos))
    print('Current position [mm]= {}'.format(stage.get_real_value_from_device_unit(pos, UnitType.DISTANCE)))

    # home the device and wait for the move to finish
    stage.home()
    while stage.get_position() != 0:
        time.sleep(stage.polling_duration()*1e-3)
        print('Going home... at position index {}'.format(stage.get_position()))

    time.sleep(1)

    # move to 30 mm and wait for the move to finish
    new_position = stage.get_device_unit_from_real_value(30.0, UnitType.DISTANCE)
    stage.move_to_position(new_position)
    while stage.get_position() != new_position:
        time.sleep(stage.polling_duration()*1e-3)
        print('Move to 30 mm [device units={}]... at position index {}'.format(new_position, stage.get_position()))

    pos = stage.get_position()
    print('Position [device units]= {}'.format(pos))
    print('Position [real-world units]= {}'.format(stage.get_real_value_from_device_unit(pos, UnitType.DISTANCE)))

    # close the connection
    stage.stop_polling()
    stage.close()

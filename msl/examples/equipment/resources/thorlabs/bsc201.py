"""
This example communicates with a Thorlabs Benchtop Stepper Motor Controller (BSC201).
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend
    from msl.equipment.resources.thorlabs.kinesis.enums import UnitType

    # ensure that the Kinesis folder is available on the PATH
    os.environ['PATH'] += os.pathsep + 'C:/Program Files/Thorlabs/Kinesis'

    # rather than reading the EquipmentRecord from a database we can create the EquipmentRecord in a script
    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='BSC201',
        serial='40876748',  # update the serial number for your device
        connection=ConnectionRecord(
            address='SDK::BenchtopStepperMotor::Thorlabs.MotionControl.Benchtop.StepperMotor.dll',
            backend=Backend.MSL,
        )
    )

    # connect to the Stepper Motor
    motor = record.connect()
    print('Connected to {}'.format(motor))

    # set the channel number of the Stepper Motor to communicate with
    channel = 1

    # read the move parameters
    velocity, acceleration = motor.get_vel_params(channel)
    jog_size = motor.get_jog_step_size(channel)

    # convert the move parameters to real-world units
    print('jog_size: {}'.format(motor.get_real_value_from_device_unit(channel, jog_size, UnitType.DISTANCE)))
    print('velocity: {}'.format(motor.get_real_value_from_device_unit(channel, velocity, UnitType.VELOCITY)))
    print('acceleration: {}'.format(motor.get_real_value_from_device_unit(channel, acceleration, UnitType.ACCELERATION)))

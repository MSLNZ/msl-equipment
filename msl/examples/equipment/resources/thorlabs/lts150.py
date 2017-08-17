"""
This example shows how to communicate with Thorlabs LTS150, 150-mm Translation Stage with Stepper Motor.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import time
    from logging.config import fileConfig

    from msl.examples.equipment import EXAMPLES_DIR
    from msl.equipment.constants import Backend
    from msl.equipment import EquipmentRecord, ConnectionRecord

    log_config = os.path.join(EXAMPLES_DIR, 'logging-config.ini')
    fileConfig(log_config, disable_existing_loggers=False)

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

    info = stage.get_hardware_info()
    print('Found device: {}'.format(info.notes))

    stage.start_polling(200)
    time.sleep(1)

    print('Current position = {}'.format(stage.get_position()))

    print('Go home...')
    stage.home()

    current_position = stage.get_position()
    print('Current position = {}'.format(current_position))
    print('Max Velocity, Acceleration = {}, {}'.format(*stage.get_vel_params()))

    new_position = current_position + 1000000
    print('Move to {}'.format(new_position))
    stage.move_to_position(new_position)
    print('Current position = {}'.format(stage.get_position()))

    stage.stop_polling()

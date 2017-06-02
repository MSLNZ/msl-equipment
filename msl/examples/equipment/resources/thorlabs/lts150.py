"""
This example shows how to communicate with Thorlabs LTS150, 150-mm Translation Stage with Stepper Motor.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import time
    from logging.config import fileConfig

    from msl.equipment.config import Config
    from msl.examples.equipment import EXAMPLES_DIR

    log_config = os.path.join(EXAMPLES_DIR, 'logging-config.ini')
    fileConfig(log_config, disable_existing_loggers=False)

    # the 'config.xml' file contains
    # <equipment alias="stage" manufacturer="Thorlabs" model="LTS150/M"/>
    # and the appropriate <equipment_connections> and <equipment_registers> XML elements
    db = Config('C:/Users/j.borbely/code/git/few-photons/config.xml').database()

    stage = db.equipment['stage'].connect()
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

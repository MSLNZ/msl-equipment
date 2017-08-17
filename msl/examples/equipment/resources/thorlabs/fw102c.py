"""
This example shows how to communicate with Thorlabs FW102C Series and 
FW212C Series Motorized Filter Wheels.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    from logging.config import fileConfig

    from msl.examples.equipment import EXAMPLES_DIR
    from msl.equipment.constants import Backend
    from msl.equipment import EquipmentRecord, ConnectionRecord

    log_config = os.path.join(EXAMPLES_DIR, 'logging-config.ini')
    fileConfig(log_config, disable_existing_loggers=False)

    # you must update the following values
    dll_path = r'C:\Program Files\Thorlabs\FilterWheel102_win64.dll'
    serial_number = 'TP01418262-6535'
    port = 'COM4'

    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='FW212CNEB',
        serial=serial_number,
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::FilterWheel102C::{}'.format(dll_path),
            properties={'port': port},
        ),
    )

    wheel = record.connect()

    print(wheel)
    position = wheel.get_position()
    print('The current position is: {}'.format(position))
    wheel.set_position(position+1)
    print('The current position is: {}'.format(wheel.get_position()))

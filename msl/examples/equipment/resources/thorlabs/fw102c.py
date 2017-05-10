"""
This example shows how to communicate with Thorlabs FW102C Series and 
FW212C Series Motorized Filter Wheels.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    from logging.config import fileConfig
    from msl.examples.equipment import EXAMPLES_DIR

    log_config = os.path.join(EXAMPLES_DIR, 'logging-config.ini')
    fileConfig(log_config, disable_existing_loggers=False)

    from msl.equipment.constants import Backend
    from msl.equipment import EquipmentRecord, ConnectionRecord

    path = r'C:\Users\j.borbely\Downloads\AppNotes_FW102C_v400\AppNotes_FW102C\LabVIEW\Thorlabs_FW102C\Library\FilterWheel102_win64.dll'

    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='FW212CNEB',
        serial='TP01812252',
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::FilterWheel102C::{}'.format(path),
            properties={'port': 'COM3'},
        ),
    )

    wheel = record.connect()

    print(wheel)
    position = wheel.get_position()
    print('The current position is: {}'.format(position))
    wheel.set_position(position+1)
    print('The current position is: {}'.format(wheel.get_position()))

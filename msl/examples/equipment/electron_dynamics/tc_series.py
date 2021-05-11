"""
Example showing how to communicate with a TC Series
Temperature Controller from Electron Dynamics Ltd.
"""
from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='Electron Dynamics',
    model='TC Lite',
    connection=ConnectionRecord(
        address='COM5',
        backend=Backend.MSL,
    )
)

# connect to the Temperature Controller
tc = record.connect()

# get all available information about the Temperature Controller
print('alarm: {}'.format(tc.get_alarm()))
print('control: {}'.format(tc.get_control()))
print('sensor: {}'.format(tc.get_sensor()))
print('output: {}'.format(tc.get_output()))
print('status: {}'.format(tc.get_status()))
print('setpoint: {}'.format(tc.get_setpoint()))

# set the sensor to be PT100
tc.set_sensor(1, 0, 0.722, 0, 'C', 0)

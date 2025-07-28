"""
This example shows how to communicate with Thorlabs
KDC101, KCube DC Servo.
"""
import os
from pprint import pprint

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.resources.thorlabs import MotionControl

# ensure that the Kinesis folder is available on PATH
os.environ['PATH'] += os.pathsep + 'C:/Program Files/Thorlabs/Kinesis'

record = EquipmentRecord(
    manufacturer='Thorlabs',
    model='KDC101',
    serial='27251265',  # update for your device
    connection=ConnectionRecord(
        backend=Backend.MSL,
        address='SDK::Thorlabs.MotionControl.KCube.DCServo.dll',
    ),
)


def wait():
    motor.clear_message_queue()
    while True:
        status = motor.convert_message(*motor.wait_for_message())['id']
        if status == 'Homed' or status == 'Moved':
            break
        position = motor.get_position()
        real = motor.get_real_value_from_device_unit(position, 'DISTANCE')
        print('  at position {} [device units] {:.3f} [real-world units]'.format(position, real))


# avoid the FT_DeviceNotFound error
MotionControl.build_device_list()

# connect to the KCube DC Servo
motor = record.connect()
print('Connected to {}'.format(motor))

# load the configuration settings, so that we can call
# the get_real_value_from_device_unit() method
motor.load_settings()

# start polling at 200 ms
motor.start_polling(200)

# home the device
print('Homing...')
motor.home()
wait()
print('Homing done. At position {} [device units]'.format(motor.get_position()))

# move to position 100000
print('Moving to 100000...')
motor.move_to_position(100000)
wait()
print('Moving done. At position {} [device units]'.format(motor.get_position()))

# move by a relative amount of -5000
print('Moving by -5000...')
motor.move_relative(-5000)
wait()
print('Moving done. At position {} [device units]'.format(motor.get_position()))

# jog forwards
print('Jogging forwards by {} [device units]'.format(motor.get_jog_step_size()))
motor.move_jog('Forwards')
wait()
print('Jogging done. At position {} [device units]'.format(motor.get_position()))

# stop polling and close the connection
motor.stop_polling()
motor.disconnect()

# you can access the default settings for the motor to pass to the set_*() methods
print('\nThe default motor settings are:')
pprint(motor.settings)

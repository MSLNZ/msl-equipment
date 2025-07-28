"""
This example communicates with a Thorlabs
Filter Flipper (MFF101 or MFF102).
"""
import os
import time

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
    model='MFF101/M',  # specify MFF102 if you have the 2" version
    serial='37871232',  # update for your device
    connection=ConnectionRecord(
        backend=Backend.MSL,
        address='SDK::Thorlabs.MotionControl.FilterFlipper.dll',
    ),
)

# Build the device list before connecting to the Filter Flipper
MotionControl.build_device_list()

# connect to the Filter Flipper
flipper = record.connect()
print('Connected to {}'.format(flipper))

# wait a little bit for the Thorlabs SDK to open the serial port
time.sleep(1)

# start polling at 200 ms
flipper.start_polling(200)

position = flipper.get_position()
print('Flipper is at position {}'.format(position))

# move the flipper to the other position and wait for the move to finish
position = 1 if position == 2 else 2
print('Moving the flipper to position {}'.format(position))
flipper.move_to_position(position)
while flipper.get_position() != position:
    print('  waiting...')
    time.sleep(0.1)
print('Move done. Flipper is now at position {}'.format(flipper.get_position()))

# stop polling and close the connection
flipper.stop_polling()
flipper.disconnect()

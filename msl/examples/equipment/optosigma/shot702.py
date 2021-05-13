"""
Example showing how to communicate with a SHOT-702 (2-axis stage controller)
from OptoSigma.
"""
import time

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='OptoSigma',
    model='SHOT-702',
    connection=ConnectionRecord(
        address='COM1',  # update for your controller
        backend=Backend.MSL,
        properties=dict(
            termination='\r\n',
            timeout=2,
            baud_rate=38400,
        ),
    )
)


# callback used by the "wait" method
def show_status(*args):
    print('  position1={}, position2={}, stopped={}, is_moving={}'.format(*args))


# connect to the controller
shot = record.connect()

# move stage 1 to the home position
print('Homing...')
shot.home(1)

# wait for the stage to finish moving while printing the status to stdout
shot.wait(show_status)

# move stage 1 to a position
print('Move to 10000...')
shot.move_absolute(1, 10000)

# wait for the stage to finish moving while printing the status to stdout
shot.wait(show_status)

# move stage 1 by -1000
print('Move by -1000...')
shot.move_relative(1, -1000)

# wait for the stage to finish moving while printing the status to stdout
shot.wait(show_status)

# get the status of the stages
status = shot.status()
print('position1={}, position2={}, stopped={}, is_moving={}'.format(*status))

# start moving stage 1 at the minimum speed in the + direction for 5 seconds
print('Start moving stage 1 for 5 seconds...')
shot.move(1, '+')
time.sleep(5)

# slowly stop stage 1
print('Stopping stage 1')
shot.stop_slowly(1)

# get the status of the stages
status = shot.status()
print('position1={}, position2={}, stopped={}, is_moving={}'.format(*status))

# disconnect from the controller
shot.disconnect()

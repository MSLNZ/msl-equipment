"""Example showing how to communicate with a SHOT-702 (2-axis stage controller) from OptoSigma."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import SHOT702, optosigma


connection = Connection(
    "COM1",  # update for your controller
    manufacturer="OptoSigma",
    model="SHOT-702",
    timeout=2,
)


def print_status(status: optosigma.Status) -> None:
    """Callback function that is used by the "wait" method."""
    print(f"  p1={status.position1}, p2={status.position2}, state={status.state!r}, is_moving={status.is_moving}")


# connect to the controller
shot: SHOT702 = connection.connect()

# move stage 1 to the home position
print("Homing...")
shot.home(1)

# wait for the stage to finish moving while printing the status
shot.wait(print_status)

# move stage 1 to a position
print("Move to 10000...")
shot.move_absolute(1, 10000)

# wait for the stage to finish moving while printing the status
shot.wait(print_status)

# move stage 1 by -1000
print("Move by -1000...")
shot.move_relative(1, -1000)

# wait for the stage to finish moving while printing the status
shot.wait(print_status)

# get the status of the stages
status = shot.status()
print("position1={}, position2={}, state={}, is_moving={}".format(*status))

# start moving stage 1 at the minimum speed in the + direction for 5 seconds
print("Start moving stage 1 for 5 seconds...")
shot.move(1, "+")
time.sleep(5)

# slowly stop stage 1
print("Stopping stage 1")
shot.stop_slowly(1)

# get the status of the stages
status = shot.status()
print("position1={}, position2={}, state={}, is_moving={}".format(*status))

# disconnect from the controller
shot.disconnect()

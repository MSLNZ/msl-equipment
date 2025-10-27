"""Example showing how to communicate with a PR4000B Flow and Pressure controller from MKS."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection, Parity

if TYPE_CHECKING:
    from msl.equipment.resources import PR4000B


connection = Connection(
    "COM3",  # update for your controller
    manufacturer="MKS Instruments",
    model="PR4000BF2V2",
    baud_rate=9600,  # the baud rate can be changed on the PR4000B
    parity=Parity.ODD,  # the parity can be changed on the PR4000B
)

# connect to the controller
mks: PR4000B = connection.connect()

# get the identity of the controller
identity = mks.identity()
print(f"Identity: {identity}")

# reset to the default pressure configuration
mks.default("pressure")

# set the pressure range for channel 2 to be 133 Pa
mks.set_range(2, 133, "Pa")

# read the pressure from channel 2
pressure = mks.get_actual_value(2)
print(f"pressure: {pressure}")

# disconnect from the controller
mks.disconnect()

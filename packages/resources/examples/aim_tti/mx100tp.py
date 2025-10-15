"""Example showing how to communicate with an MX100TP DC power supply."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import MXSeries


connection = Connection(
    address="TCP::169.254.100.2::9221",  # if using the LAN port (update the IP address)
    # address="COM5", # if using the USB or RS232 port (update the port number)
    # address="GPIB::5",  # if using the GPIB port (must also disable termination characters)
    manufacturer="Aim-TTi",
    model="MX100TP",
    timeout=5,
    # termination=None, # disable termination characters if using GPIB
)

# The output channel to use
channel = 1

# Establish the connection to the DC power supply
tti: MXSeries = connection.connect()

# Turn the output on and set the voltage to 0.1 volts
tti.turn_on(channel)
tti.set_voltage(channel, 0.1)
voltage = tti.get_voltage(channel)
print(f"The output of channel {channel} is {voltage}V")

# Increment the output voltage by 0.1 volts for each iteration
tti.set_voltage_step_size(channel, 0.1)
for _ in range(10):
    tti.increment_voltage(channel)
    setpoint = tti.get_voltage_setpoint(channel)
    voltage = tti.get_voltage(channel)
    current = tti.get_current(channel)
    print(f"V_set={setpoint}V, V_out={voltage}V, I_out={current}A")
    time.sleep(0.5)

# Turn off all outputs (the multi-off feature)
tti.turn_off_multi()

# Disconnect from the DC power supply
tti.disconnect()

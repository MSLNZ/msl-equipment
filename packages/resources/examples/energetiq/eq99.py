"""Example showing how to communicate with an EQ-99 Manager from Energetiq."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import EQ99

connection = Connection(
    "COM6",  # update for your Manager
    manufacturer="Energetiq",
    model="EQ-99",
)

# connect to the Manager
eq99: EQ99 = connection.connect()

# get the total number of running hours of the lamp
print(f"Lamp runtime is {eq99.get_lamp_runtime()} hours")

# turn the output on
eq99.set_output_state(enable=True)

# wait for the lamp to turn on
t0 = time.time()
while True:
    bit_mask = eq99.condition_register()
    if bit_mask & 1 << 5:  # index 5 represents the "Lamp on" state
        print("Lamp is on")
        break

    time.sleep(1)
    dt = int(time.time() - t0)
    print(f"Elapsed time: {dt} seconds, bit mask: {bit_mask}")

# do other stuff while the lamp is on
time.sleep(5)

# turn the output off when done
eq99.set_output_state(enable=False)

# disconnect from the Manager
eq99.disconnect()

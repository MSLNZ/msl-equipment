"""Example showing how to communicate with an OMEGA iTHX Series Temperature and Humidity Chart Recorder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import ITHX


connection = Connection(
    "TCP::192.168.1.100::2000",  # update for your OMEGA iServer
    manufacturer="OMEGA",
    model="iTHX-W3",  # update for your OMEGA iServer
    timeout=2,
)

# Connect to the iServer
ithx: ITHX = connection.connect()

# Read the temperature, relative humidity and dewpoint
print(f"T {ithx.temperature()} °C")
print(f"H {ithx.humidity()} %")
print(f"DP {ithx.dewpoint(celsius=False)} °F")

# Disconnect from the iServer
ithx.disconnect()

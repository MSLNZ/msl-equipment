"""Example showing how to use a callback function with a Wavelength Meter from HighFinesse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection
from msl.equipment.resources import high_finesse_callback

if TYPE_CHECKING:
    from msl.equipment.resources import HighFinesse

# Assumes the `wlmData.dll` library is available on the PATH environment variable
# Update the `serial` value for your device
# c = Connection("SDK::wlmData", manufacturer="HighFinesse", serial="709")
c = Connection(
    r"SDK::D:\SDKs\HighFinesse\Wavelength Meter WS5 709\x64\wlmData",
    manufacturer="HighFinesse",
    serial="709",
)


@high_finesse_callback
def my_callback(serial: int, mode: int, data1: int, data2: float, switcher_timestamp: int) -> None:
    """The callback to receive measurement data.

    Args:
        serial: The serial number of the device that call the callback.
        mode: Indicates the meaning of the `data1` and `data2` parameters.
            See the `CallbackProcEx` function in the HighFinesse manual for more information.
            For example, `mode=42` corresponds to `cmiWavelength1` and `mode=14` corresponds
            to `cmiTemperature`.
        data1: Interpretation depends on `mode` (see manual).
        data2: Interpretation depends on `mode` (see manual).
        switcher_timestamp: Only applicable if `mode=203` (`cmiSwitcherChannel`), in which case
            this value is the switching timestamp. For all other `mode` values this is `0`.
    """
    print("Press ENTER to stop", serial, mode, data1, data2, switcher_timestamp)


# Connect to the wavelength meter
w: HighFinesse = c.connect()

# Make sure the High Finesse software is running (you must update the executable path)
w.run_software(f"C:/Program Files (x86)/HighFinesse/Wavelength Meter WS5 {c.serial}/wlm_ws5.exe")

# Start the measurement and register the callback function to receive data
_ = input("Press ENTER to start the measurement ")
w.start_measurement()
w.set_callback(my_callback)

# Wait for ENTER to be pressed
_ = input()

# Disconnect from the wavelength meter
w.set_callback(None)
w.stop_measurement()
w.disconnect()

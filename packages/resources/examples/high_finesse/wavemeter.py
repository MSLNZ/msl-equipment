"""Example showing how to communicate with a Wavelength Meter from HighFinesse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import HighFinesse

# Assumes the `wlmData.dll` library is available on the PATH environment variable
# Update the `serial` value for your device
c = Connection("SDK::wlmData", manufacturer="HighFinesse", serial="709")

# Connect to the Wavelength Meter
w: HighFinesse = c.connect()

# Make sure the High Finesse software is running (you must update the executable path)
w.run_software(f"C:/Program Files (x86)/HighFinesse/Wavelength Meter WS5 {c.serial}/wlm_ws5.exe")
print(w.version_info())
print(f"Auto exposure enabled? {w.auto_exposure_enabled}")
print("Exposure time =", w.get_exposure_time(), "ms")
print(f"Pulsed mode? {w.pulsed}")
print(f"Precision {w.precision!r}")

_ = input("Press ENTER to start a measurement (wait for the software window to finish loading) ")
w.start_measurement()

# Use fine precision
w.precision = w.Precision.Fine

# Wait for a valid wavelength to be measured and for the exposure time to be stable for 2 seconds
w.wait(2)

print("Wavelength", w.wavelength(), "nm")
print("Wavelength", w.wavelength(w.Unit.PhotonEnergy), "eV")
print("Temperature", w.temperature, "°C")

# Disconnect from the Wavelength Meter
w.stop_measurement()
w.disconnect()

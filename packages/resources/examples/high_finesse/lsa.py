"""Example showing how to communicate with a Laser Spectrum Analyser from HighFinesse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import HighFinesse


# Assumes the `wlmData.dll` library is available on the PATH environment variable
# Update the `serial` value for your device
c = Connection("SDK::wlmData", manufacturer="HighFinesse", serial="2095")

# Connect to the Laser Spectrum Analyser
lsa: HighFinesse = c.connect()

# Make sure the High Finesse software is running (you must update the executable path)
lsa.run_software(f"C:/Program Files (x86)/HighFinesse/Laser Spectrum Analyser - LSA {c.serial}/LSA.exe")
print(lsa.version_info())
print(f"Analysis mode enabled? {lsa.analysis_mode_enabled}")
print(f"Auto exposure enabled? {lsa.auto_exposure_enabled}")
print("Exposure time(1) =", lsa.get_exposure_time(), "ms")
print("Exposure time(2) =", lsa.get_exposure_time(index=2), "ms")
print(f"Pulsed mode? {lsa.pulsed}")
print(f"Precision {lsa.precision!r}")

# Tell the device to select the wavelength range that can measure the specified wavelength
# Here we expect to measure light at a wavelength of 532 nm
lsa.select_wavelength_range(532)

# Use fine precision
lsa.precision = lsa.Precision.Fine

# Enable linewidth measurements
lsa.linewidth_enabled = True

_ = input("Press ENTER to start a measurement (wait for the software window to finish loading) ")
lsa.start_measurement()

# Wait for a valid wavelength to be measured and for the exposure time to be stable for 2 seconds
lsa.wait(2)

print("Wavelength", lsa.wavelength(), "nm")
print("Wavelength", lsa.wavelength(lsa.Unit.PhotonEnergy), "eV")
print("Linewidth", lsa.linewidth(), "nm")
print("Pressure", lsa.pressure, "mbar")
print("Temperature", lsa.temperature, "°C")

# Disconnect from the Laser Spectrum Analyser
lsa.stop_measurement()
lsa.disconnect()

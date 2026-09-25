"""Example showing how to communicate with a Wavelength Meter from HighFinesse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import HighFinesse

# Assumes the `wlmData.dll` library is available on the PATH environment variable
# Update the `serial` value for your device
# c = Connection("SDK::wlmData", manufacturer="HighFinesse", serial="709")
c = Connection(
    r"SDK::D:\SDKs\HighFinesse\Wavelength Meter WS5 709\x86\wlmData",
    manufacturer="HighFinesse",
    serial="709",
)

# Connect to the wavelength meter
w: HighFinesse = c.connect()

# Make sure the High Finesse software is running (you must update the executable path)
w.run_software(f"C:/Program Files (x86)/HighFinesse/Wavelength Meter WS5 {c.serial}/wlm_ws5.exe")
print(w.version_info())

_ = input("Press ENTER when the HighFinesse software has finished loading ")
print(w.auto_exposure_state)
w.auto_exposure_state = not w.auto_exposure_state
print(w.auto_exposure_state)

print(w.get_exposure_time())
w.set_exposure_time(10)
print(w.get_exposure_time())

_ = input("Press ENTER to start a measurement ")
w.start_measurement()

_ = input("Press ENTER to fetch the wavelength and temperature ")
wavelength = w.wavelength()
print(wavelength, "nm")
print(w.convert_unit(wavelength, w.WLMUnit.PhotonEnergy), "eV")
print(w.temperature(), "°C")
print(w.interferometer_data(0))

# Disconnect from the wavelength meter
w.stop_measurement()
w.disconnect()

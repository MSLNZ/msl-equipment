"""Example showing how to communicate with an Optronic Laboratories 756 UV-VIS spectroradiometer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import OL756


connection = Connection(
    "SDK::OL756SDKACTIVEX.OL756SDKActiveXCtrl.1",
    manufacturer="Optronic Laboratories Inc",
    model="756",
    serial="05001009",
    mode=1,  # connection mode: 0=RS232, 1=USB
    com_port=1,  # the COM port number (if using RS232 mode)
)

# Connect to the spectroradiometer
ol756: OL756 = connection.connect()

# Load the settings from flash memory
ol756.import_registry()
ol756.read_ol756_flash_settings()

# Get some information from the spectroradiometer
start = ol756.get_start_wavelength()
end = ol756.get_ending_wavelength()
increment = ol756.get_increment()
print(f"SDK version: {ol756.get_ocx_version()}")
print(f"Wavelength scan range: {start} .. {end} @ {increment} nm")

# Acquire a scan
ol756.send_down_parameters(0)  # Point to point scan. Must be called before take_point_to_point_measurement
ol756.take_point_to_point_measurement(0)  # Irradiance type

# Get the data
data = ol756.get_signal_array()
print(data)

# Disconnect from the spectroradiometer
ol756.disconnect()

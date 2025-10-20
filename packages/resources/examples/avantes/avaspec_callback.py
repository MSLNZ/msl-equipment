"""Example showing how to use a callback with an AvaSpec-2048L spectrometer.

The AvaSpec shared library may require a Visual C++ Redistributable Package to be installed (on Windows).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from msl.equipment import Connection
from msl.equipment.resources import avantes

if TYPE_CHECKING:
    from ctypes import _Pointer, c_int32  # pyright: ignore[reportPrivateUsage]

    from msl.equipment.resources import AvaSpec


@avantes.avaspec_callback
def callback(handle: _Pointer[c_int32], info: _Pointer[c_int32]) -> None:
    """This function is called every time a measurement scan is available."""
    print(f"The DLL handle is: {handle.contents.value}")
    if info.contents.value == 0:  # equals 0 if everything is okay (see manual)
        print(f"  callback data: {ava.get_data()}")


connection = Connection(
    "SDK::C:/Path/to/avaspecx64.dll",  # update path to avaspec library
    manufacturer="Avantes",
    model="AvaSpec-2048L",  # update for your device
    serial="1807344U1",  # update for your device
)

# initializes the Avantes SDK and establishes the connection to the spectrometer
ava: AvaSpec = connection.connect()

# get the number of pixels that the spectrometer has
num_pixels = ava.get_num_pixels()
print(f"The spectrometer has {num_pixels} pixels")

# get the wavelength value of each pixel
wavelengths = ava.get_lambda()

# enable the 16-bit AD converter
ava.use_high_res_adc(enable=True)

# prepare the measurement type of the spectrometer
# (the values of just a few parameters are updated here, see the manual for more details)
cfg = avantes.MeasConfigType()
cfg.m_StopPixel = num_pixels - 1
cfg.m_IntegrationTime = 5  # in milliseconds
cfg.m_NrAverages = 1  # number of averages
ava.prepare_measure(cfg)

# start continuous measurements
# (use a callback function to be notified when a measurement is ready)
ava.measure_callback(-1, callback)

# get as many scans as possible for 2 seconds
time.sleep(2)

# stop continuous measurements
ava.stop_measure()

# disconnect from the spectrometer
ava.disconnect()

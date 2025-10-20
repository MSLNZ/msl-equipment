"""Example showing how to communicate with an AvaSpec-2048L spectrometer.

The AvaSpec shared library may require a Visual C++ Redistributable Package to be installed (on Windows).
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from msl.equipment import Connection
from msl.equipment.resources import avantes

if TYPE_CHECKING:
    from msl.equipment.resources import AvaSpec

# You can either specify the full path to the SDK
# (e.g., C:/AvaSpecX64-DLL_9.7/avaspecx64.dll) in the Connection address,
# or, you can add the directory where the avaspecx64 library file is located
# to your PATH environment variable
os.environ["PATH"] += os.pathsep + r"C:\AvaSpecX64-DLL_9.7"

connection = Connection(
    "SDK::avaspecx64.dll",  # The directory where the DLL is located is available on PATH
    manufacturer="Avantes",
    model="AvaSpec-2048L",  # update for your device
    serial="1807344U1",  # update for your device
)

# initializes the Avantes SDK and establishes the connection to the spectrometer
ava: AvaSpec = connection.connect()

# get the version of the SDK
print(f"DLL version: {ava.get_dll_version()}")

# print (some of) the device information about the spectrometer
print("DeviceConfigType parameters:")
params = ava.get_parameter()
print(f"  m_Len: {params.m_Len}")
print(f"  m_ConfigVersion: {params.m_ConfigVersion}")
print(f"  m_aUserFriendlyId: {params.m_aUserFriendlyId}")
print(f"  m_Detector.m_DefectivePixels: {list(params.m_Detector.m_DefectivePixels)}")
print(f"  m_Detector.m_ExtOffset: {params.m_Detector.m_ExtOffset}")
print(f"  m_Detector.m_Gain: {list(params.m_Detector.m_Gain)}")
print(f"  m_Detector.m_NLEnable: {params.m_Detector.m_NLEnable}")
print(f"  m_Detector.m_NrPixels: {params.m_Detector.m_NrPixels}")
print(f"  m_Detector.m_Offset: {list(params.m_Detector.m_Offset)}")
print(f"  m_Detector.m_SensorType: {params.m_Detector.m_SensorType}")
print(f"  m_Detector.m_aFit: {list(params.m_Detector.m_aFit)}")
print(f"  m_Detector.m_aHighNLCounts: {params.m_Detector.m_aHighNLCounts}")
print(f"  m_Detector.m_aLowNLCounts: {params.m_Detector.m_aLowNLCounts}")
print(f"  m_Detector.m_aNLCorrect: {list(params.m_Detector.m_aNLCorrect)}")
print(f"  ...m_SmoothPix: {params.m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothPix}")
print(f"  ...m_SmoothModel: {params.m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothModel}")
# ... continue printing parameters ...

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

# start 1 measurement, wait until the measurement is finished, then get the data
ava.measure(1)
while not ava.poll_scan():
    time.sleep(0.01)
tick_count, data = ava.get_data()

# we can get the Dark Pixel data after we call get_data()
print(f"Dark Pixel data: {ava.get_dark_pixel_data()}")

print("Measurement data:", data)

# disconnect from the spectrometer
ava.disconnect()

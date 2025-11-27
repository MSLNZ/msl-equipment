"""Example showing how to communicate with a WinCamD beam-profiling camera from DataRay.

Tested with the WinCamD-LCM-8.0E45 (x64) software version.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from msl.equipment import Connection

if TYPE_CHECKING:
    from msl.equipment.resources import WinCamD

connection = Connection(
    "SDK::DATARAYOCX",
    manufacturer="DataRay",
    model="WinCamD",
    # plateau_uniformity=True,  # these are some examples of the properties that can be specified
    # full_scale_filter=0.5,
)

# Connect to the camera (a GUI will be displayed).
# The GUI must remain open to have access to the DataRay OCX library.
# The text "Error in oglInitialize invalid operation" might be printed, ignore it.
camera: WinCamD = connection.connect()

# Wait until the camera has been configured (e.g., set the image size, ROI, major/minor mode, ...)
camera.wait_to_configure()

# Capture an image,
camera.capture()

# and then you can get information about the image
print("image", camera.image)
print("profile_x", camera.profile_x)
print("profile_y", camera.profile_y)
print("pixel_size", camera.pixel_size)
print("centroid", camera.centroid)
print("roi", camera.roi)
print("xc", camera.xc)
print("xg", camera.xg)
print("xp", camera.xp)
print("yc", camera.yc)
print("yg", camera.yg)
print("yp", camera.yp)
print("major", camera.major)
print("mean", camera.mean)
print("minor", camera.minor)
print("orientation", camera.orientation)
print("plateau_uniformity", camera.plateau_uniformity)
print("homogeneity", camera.homogeneity)
print("adc_peak_percent", camera.adc_peak_percent)
print("effective_2w", camera.effective_2w)
print("ellipticity", camera.ellipticity)
print("exposure_time", camera.exposure_time)

# You can also access properties of the SDK
print("ImagerGain", camera.sdk.ImagerGain)
print("CameraType", camera.sdk.CameraType())

# Disconnect from the camera (also closes the GUI)
camera.disconnect()

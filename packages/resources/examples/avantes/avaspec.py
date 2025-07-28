"""
Example showing how to communicate with an AvaSpec-2048L spectrometer.
"""
import time

# if matplotlib is available then plot the data
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='Avantes',
    model='AvaSpec-2048L',  # update for your device
    serial='1807344U1',  # update for your device
    connection=ConnectionRecord(
        address='SDK::D:/AvaSpecX64-DLL_9.7/avaspecx64.dll',  # update the path to the DLL file
        backend=Backend.MSL,
    )
)

# initializes the Avantes SDK and establishes the connection to the spectrometer
ava = record.connect()

# get the version of the SDK
print('DLL version: {}'.format(ava.get_dll_version()))

# print (some of) the device information about the spectrometer
print('DeviceConfigType parameters:')
params = ava.get_parameter()
print('  m_Len: %d' % params.m_Len)
print('  m_ConfigVersion: %d' % params.m_ConfigVersion)
print('  m_aUserFriendlyId: %r' % params.m_aUserFriendlyId)
print('  m_Detector.m_DefectivePixels: %r' % [val for val in params.m_Detector.m_DefectivePixels])
print('  m_Detector.m_ExtOffset: %f' % params.m_Detector.m_ExtOffset)
print('  m_Detector.m_Gain: %r' % [val for val in params.m_Detector.m_Gain])
print('  m_Detector.m_NLEnable: %r' % params.m_Detector.m_NLEnable)
print('  m_Detector.m_NrPixels: %d' % params.m_Detector.m_NrPixels)
print('  m_Detector.m_Offset: %r' % [val for val in params.m_Detector.m_Offset])
print('  m_Detector.m_SensorType: %d' % params.m_Detector.m_SensorType)
print('  m_Detector.m_aFit: %r' % [val for val in params.m_Detector.m_aFit])
print('  m_Detector.m_aHighNLCounts: %f' % params.m_Detector.m_aHighNLCounts)
print('  m_Detector.m_aLowNLCounts: %f' % params.m_Detector.m_aLowNLCounts)
print('  m_Detector.m_aNLCorrect: %r' % [val for val in params.m_Detector.m_aNLCorrect])
print('  m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothPix: %d' % params.m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothPix)
print('  m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothModel: %d' % params.m_Irradiance.m_IntensityCalib.m_Smoothing.m_SmoothModel)
print('  m_Irradiance.m_IntensityCalib.m_CalInttime: %d' % params.m_Irradiance.m_IntensityCalib.m_CalInttime)
# ... continue printing parameters ...

# get the number of pixels that the spectrometer has
num_pixels = ava.get_num_pixels()
print('The spectrometer has %d pixels' % num_pixels)

# get the wavelength value of each pixel
wavelengths = ava.get_lambda()

# enable the 16-bit AD converter
ava.use_high_res_adc(True)

# prepare the measurement type of the spectrometer
# (the values of just a few parameters are updated here, see the manual for more details)
cfg = ava.MeasConfigType()
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
print('Dark Pixel data: {}'.format(ava.get_dark_pixel_data()))

print('measurement data:', data)
if plt is not None:
    plt.title('Time label (tick counts): %d' % tick_count)
    plt.xlabel('Wavelength [nm]')
    plt.ylabel('ADC')
    plt.plot(wavelengths, data, 'bo')
    plt.show()

# disconnect from the spectrometer
ava.disconnect()

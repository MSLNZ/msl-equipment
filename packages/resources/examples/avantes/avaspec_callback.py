"""
Example showing how to use a callback with an AvaSpec-2048L spectrometer.
"""
import sys
import time

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.resources.avantes import MeasureCallback

# You can either add the directory where the avaspecx64.dll file is located
# to sys.path or specify the full path to the SDK in the address attribute
sys.path.append('D:/AvaSpecX64-DLL_9.7')

record = EquipmentRecord(
    manufacturer='Avantes',
    model='AvaSpec-2048L',  # update for your device
    serial='1807344U1',  # update for your device
    connection=ConnectionRecord(
        # only specify the SDK filename since the directory was added to sys.path (see above)
        address='SDK::avaspecx64.dll',
        backend=Backend.MSL,
    )
)


@MeasureCallback
def callback_fcn(handle, info):
    # this function will be called every time a measurement scan is available
    print('The DLL handle is: {}'.format(handle.contents.value))
    if info.contents.value == 0:  # equals 0 if everything is okay (see manual)
        print('  callback data: {}'.format(ava.get_data()))


# initializes the Avantes SDK and establishes the connection to the spectrometer
ava = record.connect()

# get the number of pixels that the spectrometer has
num_pixels = ava.get_num_pixels()
print('The spectrometer has {} pixels'.format(num_pixels))

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

# start continuous measurements
# (use a callback function to be notified when a measurement is ready)
ava.measure_callback(-1, callback_fcn)

# get as many scans as possible for 2 seconds
time.sleep(2)

# stop continuous measurements
ava.stop_measure()

# disconnect from the spectrometer
ava.disconnect()

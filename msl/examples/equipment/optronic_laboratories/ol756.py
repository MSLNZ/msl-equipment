"""
Example showing how to communicate with an
Optronic Laboratories 756 UV-VIS spectroradiometer.
"""
from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

# if matplotlib is available then plot the results
try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    plt = None


record = EquipmentRecord(
    manufacturer='Optronic Laboratories Inc',
    model='756',
    serial='05001009',
    connection=ConnectionRecord(
        address='SDK::OL756SDKACTIVEX.OL756SDKActiveXCtrl.1',
        backend=Backend.MSL,
        parameters={
            'mode': 1,  # connection mode: 0=RS232, 1=USB
            'com_port': 1,  # the COM port number if using RS232 mode
        }
    )
)

# connect to the spectroradiometer
ol756 = record.connect()

# load the settings from flash memory
ol756.import_registry()
ol756.read_ol756_flash_settings()

# get some information from the spectroradiometer
start = ol756.get_start_wavelength()
end = ol756.get_ending_wavelength()
increment = ol756.get_increment()
print('SDK version: {}'.format(ol756.get_ocx_version()))
print('Wavelength scan range: {} .. {} @ {} nm'.format(start, end, increment))

# acquire a scan
measurement_type = 0  # Irradiance
scan_mode = 0  # Point to point scan
ol756.send_down_parameters(scan_mode)  # must be called before take_point_to_point_measurement
ol756.take_point_to_point_measurement(measurement_type)

# get the data
data = ol756.get_signal_array()
print(data)
if plt is not None:
    wavelengths = np.arange(start, end + increment, increment)
    plt.plot(wavelengths, data, 'bo')
    plt.show()

# disconnect from the spectroradiometer
ol756.disconnect()

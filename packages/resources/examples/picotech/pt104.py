"""
Example showing how to communicate with a PT-104 Data Logger
from Pico Technology.

This examples assumes that a voltage is applied to channel 1
and a PT100 is connected to channel 2.
"""
import os
import time

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='PicoTech',
    model='PT-104',
    serial='GQ840/132',  # change for your device
    connection=ConnectionRecord(
        address='SDK::usbpt104',
        backend=Backend.MSL,
        properties=dict(
            ip_address='192.168.1.100:1234',  # optional: change for your device
            open_via_ip=False,  # optional: True - connect via IP address, False - connect via USB port
        )
    )
)

# optional: ensure that the PicoTech DLLs are available on PATH
os.environ['PATH'] += os.pathsep + r'C:\Program Files\Pico Technology\SDK\lib'

# connect to the PT-104
pt104 = record.connect()

# get all available information about the PT-104
info = pt104.get_unit_info()
print(info)

# only get the date that the PT-104 was last calibrated
info = pt104.get_unit_info('cal_date', include_name=False)
print('The PT-104 was last calibrated on ' + info)

# get the IP details
details = pt104.get_ip_details()
print('IP details {}: '.format(details))

# configure channel 1 to be single-ended voltage from 0 to 2.5 V
pt104.set_channel(1, pt104.DataType.SINGLE_ENDED_TO_2500MV, 2)

# configure channel 2 to be a 4-wire PRT, PT100
pt104.set_channel(2, pt104.DataType.PT100, 4)

for i in range(10):
    # Wait for the samples to be available
    # A measurement cycle takes about 1 second per active channel
    # 2 channels are active, so we should wait at least 2 seconds
    time.sleep(3)

    # read the value of channel 1
    ch1 = pt104.get_value(1)

    # read the value of channel 2
    ch2 = pt104.get_value(2)

    # for the SINGLE_ENDED_TO_2500MV configuration the scaling factor is 10 nV
    print('Loop {}, Voltage {}'.format(i, ch1 * 10e-9))

    # for the PT100 configuration the scaling factor is 1/1000 deg C
    print('Loop {}, Temperature {}'.format(i, ch2 * 1e-3))

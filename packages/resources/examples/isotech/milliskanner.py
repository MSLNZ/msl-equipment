"""
Example showing how to communicate with an IsoTech milliK Precision Thermometer,
with any number of connected millisKanners.
"""
import logging
logging.basicConfig(level=logging.INFO)

from msl.equipment import ConnectionRecord, EquipmentRecord


record = EquipmentRecord(
    manufacturer='IsoTech',
    model='milliK',
    connection=ConnectionRecord(
        address='COM9',  # change for your device
        timeout=5,
        properties={
            'baud_rate': 9600,
            'parity': None,
            'start_bits': 1,
            'stop_bits': 1,
            'data_bits': 8,
        }  # Optional: change for your device
    )
)

thermometer = record.connect()

# Print information about the device
print('Number of devices connected:', thermometer.num_devices)
print('Connected devices:', thermometer.connected_devices)
print('Available channel numbers:', thermometer.channel_numbers)

# Configure channels using approximate resistance values for each channel
r = [13000, 470, 220, 820, 3300, 100, 1800, 100]
for i, res in enumerate(r, start=10):  # here the sensors are all on the first millisKanner only
    thermometer.configure_resistance_measurement(channel=i, meas_range=res, norm=True, fourwire=True)

# Read resistance for a specific channel, returning n readings
i = 13
print(f'Resistance value for Channel {i}:', thermometer.read_channel(i, n=5))

# print(thermometer.channel_configuration)

# Once the desired channels have been configured, then you can read them all at once
ch, res = thermometer.read_all_channels()
print("Configured channels:", ch)
print('Resistance values:', res)

# Disconnect from the milliK device and return the device to LOCAL mode
thermometer.disconnect()

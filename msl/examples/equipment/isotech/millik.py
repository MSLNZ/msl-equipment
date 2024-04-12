"""
Example showing how to communicate with an IsoTech milliK Precision Thermometer,
connected via ethernet.
"""
import logging
logging.basicConfig(level=logging.INFO)

from msl.equipment import ConnectionRecord, EquipmentRecord


record = EquipmentRecord(
    manufacturer='IsoTech',
    model='milliK',
    connection=ConnectionRecord(
        address='TCP::10.12.102.30::1000',
        timeout=5,
    )
)

thermometer = record.connect()

# Print information about the device
print('Number of devices connected:', thermometer.num_devices)
print('Connected devices:', thermometer.connected_devices)
print('Available channel numbers:', thermometer.channel_numbers)

# Configure channels using approximate resistance values for each channel
r = [130, 13000]
for i, res in enumerate(r, start=1):
    thermometer.configure_resistance_measurement(channel=i, meas_range=res, norm=True, fourwire=False)

# Read resistance for a specific channel, returning n readings
i = 2
print(f'Resistance value for Channel {i}:', thermometer.read_channel(i, n=5))

# If all channels have been configured, then you can read them all at once
ch, res = thermometer.read_all_channels()
print("Configured channels:", ch)
print('Resistance values:', res)

# Disconnect from the milliK device and return the device to LOCAL mode
thermometer.disconnect()

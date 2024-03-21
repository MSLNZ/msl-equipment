"""
Example showing how to communicate with an IsoTech milliK Precision Thermometer,
with any number of connected millisKanners.
"""
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
            'termination': '\r'
        }  # Optional: change for your device
    )
)

thermometer = record.connect()

# Read information about the device
print('Number of devices connected:', thermometer.num_devices)
print('Connected devices:', thermometer.connected_devices)
print('Available channel numbers:', thermometer.channel_numbers)

# Read the current resistance values using a resistance value for thermistors
print('Current resistance value for Channel 1:', thermometer.resistance(1, resis=20000, current='norm', wire=4))
print('Current resistance values for all channels:', thermometer.read_all_channels(resis=20000, current='norm', wire=4))

# Disconnect from the device and return the device to LOCAL mode
thermometer.close_connection()

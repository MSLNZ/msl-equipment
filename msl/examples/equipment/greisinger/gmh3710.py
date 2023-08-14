"""
Example showing how to communicate with an GMH3710 thermometer from Greisinger, GHM Group.
"""
from msl.equipment import ConnectionRecord, EquipmentRecord

record = EquipmentRecord(
    manufacturer='Greisinger',
    model='GMH3710-GE',
    connection=ConnectionRecord(
        address='COM4',  # change for your device
        timeout=2,
        # properties={'gmh_address': 11}  # Optional: change for your device
    )
)

thermometer = record.connect()

# Read information about the device
unit = thermometer.unit()
print('Current value', thermometer.value(), unit)
print('Minimum value', thermometer.min_value(), unit)
print('Maximum value', thermometer.max_value(), unit)
print('Measurement range', thermometer.measurement_range())
print('Display range', thermometer.display_range())
print('Scale correction', thermometer.scale_correction())
print('Offset correction', thermometer.offset_correction())
print('Channel count', thermometer.channel_count())
print('Power-off time', thermometer.power_off_time())
print('Resolution', thermometer.resolution())
print('Status bits', thermometer.status())
print('ID (serial) number', thermometer.id_number())
print('Firmware version', thermometer.firmware_version())

# Clears the minimum and maximum values that are stored in the device
# thermometer.clear_min_value()
# thermometer.clear_max_value()

# Sets the power-off time to 30 minutes
# thermometer.set_power_off_time(30)

# Disconnect from the device
thermometer.disconnect()

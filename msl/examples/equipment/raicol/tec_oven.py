"""
Example showing how to control a TEC (Peltier-based) oven from Raicol Crystals.
"""
import time

from msl.equipment import ConnectionRecord
from msl.equipment import EquipmentRecord

record = EquipmentRecord(
    manufacturer='Raicol Crystals',
    model='TEC 20-60',
    connection=ConnectionRecord(
        address='COM4',  # update for your device
    )
)

# connect to the TEC controller
tec = record.connect()

# set the setpoint temperature, in Celsius
tec.set_setpoint(25.0)

# get the setpoint temperature
print('setpoint=', tec.get_setpoint())

# turn the TEC on
tec.on()

# read the current temperature
for _ in range(30):
    time.sleep(1)
    print('temperature=', tec.temperature())

# turn the TEC off
tec.off()

# disconnect from the TEC controller
tec.disconnect()

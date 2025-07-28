"""
Example showing how to communicate with an MX100TP DC power supply.
"""
import time

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='Aim-TTi',
    model='MX100TP',
    connection=ConnectionRecord(
        address='TCP::192.168.1.70::9221',  # if using the LAN port
        # address='COM5',  # if using the USB or RS232 port
        # address='Prologix::192.168.1.71::1234::6',  # if using a Prologix GPIB-ETHERNET Controller
        backend=Backend.MSL,
        timeout=10,
    )
)

# the output channel to use
channel = 1

# establish the connection to the DC power supply
tti = record.connect()

# turn the output on and set the voltage to 0.1 volts
tti.turn_on(channel)
tti.set_voltage(channel, 0.1)
voltage = tti.get_voltage(channel)
print('The output of channel {} is {}V'.format(channel, voltage))

# increment the output voltage by 0.1 volts for each iteration
tti.set_voltage_step_size(channel, 0.1)
for i in range(10):
    tti.increment_voltage(channel)
    setpoint = tti.get_voltage_setpoint(channel)
    voltage = tti.get_voltage(channel)
    current = tti.get_current(channel)
    print('Vset={}V, Vout={}V, Iout={}A'.format(setpoint, voltage, current))
    time.sleep(0.5)

# turn off all outputs (the multi-off feature)
tti.turn_off_multi()

# disconnect from the DC power supply
tti.disconnect()

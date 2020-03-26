"""
Example showing how to communicate with an MX100TP DC power supply.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    record = EquipmentRecord(
        manufacturer='TTi',
        model='MX100TP',
        connection=ConnectionRecord(
            address='TCP::192.168.1.70::9221',
            backend=Backend.MSL,
            timeout=5,
        )
    )

    # the Output channel
    channel = 1

    # establish the connection to the DC power supply
    tti = record.connect()

    # turn Output 1 on and set the voltage of Output 1 to 0.1 Volts
    tti.turn_on(channel)
    tti.set_voltage(channel, 0.1)
    print('The output voltage for Output 1 is: ', tti.get_voltage(channel))

    # increment the output voltage of Output 1 by 0.02 Volts for each iteration
    tti.set_voltage_step_size(channel, 0.1)
    for i in range(10):
        tti.increment_voltage(channel)
        setpoint = tti.get_voltage_setpoint(channel)
        voltage = tti.get_voltage(channel)
        current = tti.get_current(channel)
        print('Vset={}V, Vout={}V, Iout={}A'.format(setpoint, voltage, current))
        time.sleep(0.5)

    # turn off all Outputs (the Multi-Off feature)
    tti.turn_off_multi()

    # disconnect from the DC power supply
    tti.disconnect()

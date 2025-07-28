"""
Example showing how to communicate with an EQ-99 Manager from Energetiq.
"""
import time

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='Energetiq',
    model='EQ-99',
    connection=ConnectionRecord(
        address='COM6',  # update for your controller
        backend=Backend.MSL,
    )
)

# connect to the Manager
eq99 = record.connect()

# get the total number of running hours of the lamp
print('Lamp ON time is {} hours'.format(eq99.get_lamptime()))

# turn the output on
eq99.set_output(True)

# wait for the lamp to turn on
t0 = time.time()
while True:
    value, bitmask = eq99.condition_register()
    print('Elapsed time: {:3.0f} seconds, bitmask: {}'.format(time.time() - t0, bitmask))
    if bitmask[5] == '1':  # index 5 represents the "Lamp on" state
        print('Lamp is on')
        break
    time.sleep(1)

# do other stuff while the lamp is on
time.sleep(10)

# turn the output off when done
eq99.set_output(False)

# disconnect from the Manager
eq99.disconnect()

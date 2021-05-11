"""
This example opens the connection in async mode (does not work properly in Python 2.7).
"""
import os
import time

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

record = EquipmentRecord(
    manufacturer='Pico Technology',
    model='5244B',  # update for your PicoScope
    serial='DY135/055',  # update for your PicoScope
    connection=ConnectionRecord(
        backend=Backend.MSL,
        address='SDK::ps5000a.dll',  # update for your PicoScope
        properties={'open_async': True},  # opening in async mode is done in the properties
    )
)

# optional: ensure that the PicoTech DLLs are available on PATH
os.environ['PATH'] += os.pathsep + r'C:\Program Files\Pico Technology\SDK\lib'

t0 = time.time()

scope = record.connect()
while True:
    now = time.time()
    progress = scope.open_unit_progress()
    print('Progress: {}%'.format(progress))
    if progress == 100:
        break
    time.sleep(0.02)

print('Took {:.2f} seconds to establish a connection to the PicoScope'.format(time.time()-t0))

# flash the LED light for 5 seconds
scope.flash_led(-1)
time.sleep(5)

"""
Example showing how to log the temperature, humidity and dew point
of an OMEGA iTHX Series Temperature and Humidity Chart Recorder
to a CSV file every second.

.. note::
   There is a :meth:`~msl.equipment.resources.omega.ithx.iTHX.start_logging`
   method for logging to an SQLite database.
"""
import os
import time
from datetime import datetime

from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)

# update these values for your OMEGA iServer
address = '192.168.1.200'
port = 2000
model = 'iTHX-W3'

record = EquipmentRecord(
    manufacturer='OMEGA',
    model=model,
    connection=ConnectionRecord(
        address='TCP::{}::{}'.format(address, port),
        backend=Backend.MSL,
        properties=dict(
            termination='\r',
            timeout=2
        ),
    )
)

path = os.path.join(os.path.expanduser('~'), 'ithx-logger-example.csv')

omega = record.connect()

with open(path, mode='w') as fp:
    while True:
        try:
            now = datetime.now()
            values = omega.temperature_humidity_dewpoint()
            print('{} -- {} {} {} -- Press CTRL+C to stop'.format(now, *values))
            fp.write('{},{},{},{}\n'.format(now, *values))
            time.sleep(1)
        except KeyboardInterrupt:
            break

print('Saved the log records to ' + path)

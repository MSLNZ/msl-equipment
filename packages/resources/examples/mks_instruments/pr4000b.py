"""
Example showing how to communicate with a PR4000B Flow and Pressure
controller from MKS Instruments.
"""
from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.constants import (
    Parity,
    DataBits,
)

record = EquipmentRecord(
    manufacturer='MKS Instruments',
    model='PR4000BF2V2',
    connection=ConnectionRecord(
        address='COM3',  # change for your device
        backend=Backend.MSL,
        baud_rate=9600,  # change for your device
        parity=Parity.ODD,  # change for your device
        termination=b'\r',
        timeout=5,
        data_bits=DataBits.SEVEN,
    )
)

# connect to the controller
mks = record.connect()

# get the identity of the controller
identity = mks.identity()
print('Identity: {}'.format(identity))

# reset to the default pressure configuration
mks.default('pressure')

# set the pressure range for channel 2 to be 133 Pa
mks.set_range(2, 133, 'Pa')

# get 10 readings of the pressure for channel 2
pressures = [mks.get_actual_value(2) for _ in range(10)]
print('pressure values: {}'.format(pressures))

# disconnect from the controller
mks.disconnect()

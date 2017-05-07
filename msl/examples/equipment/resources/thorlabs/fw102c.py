"""
This example shows how to communicate with Thorlabs FW102C Series and 
FW212C Series Motorized Filter Wheels.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    from msl.equipment.constants import Backend
    from msl.equipment import EquipmentRecord, ConnectionRecord

    record = EquipmentRecord(
        manufacturer='Thorlabs',
        model='FW212C',
        serial='xxxxxx',
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::FilterWheel102C::C:/Users/Flash/Desktop/AppNotes_FW102C_v400/AppNotes_FW102C/LabVIEW/Thorlabs_FW102C/Library/FilterWheel102_win64.dll',
        ),
    )

    wheel = record.connect()

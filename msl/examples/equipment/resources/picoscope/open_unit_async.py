"""
This example opens the connection in async mode.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    import time
    from msl.equipment.constants import Backend
    from msl.equipment import EquipmentRecord, ConnectionRecord

    record = EquipmentRecord(
        manufacturer='Pico Technology',
        model='5244B',
        serial='DY135/055',
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::PicoScope5000A::ps5000a',
            properties={'open_unit_async': True},  # telling the PicoScope to open in async mode is done in the properties
        )
    )

    start = time.time()

    scope = record.connect()
    while True:
        now = time.time()
        progress = scope.open_unit_progress()
        print('Progress: {}%'.format(progress))
        if progress == 100:
            break
        time.sleep(0.02)

    print('Took {:.2f} seconds to establish a connection to the PicoScope'.format(time.time()-start))

    # flash the LED light for 5 seconds
    scope.flash_led(-1)
    time.sleep(5)

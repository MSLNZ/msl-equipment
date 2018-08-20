"""
This example opens the connection in async mode (does not work properly in Python 2.7).
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    import time
    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    record = EquipmentRecord(
        manufacturer='Pico Technology',
        model='5244B',
        serial='DY135/055',
        connection=ConnectionRecord(
            backend=Backend.MSL,
            address='SDK::ps5000a',
            properties={'open_async': True},  # opening in async mode is done in the properties
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

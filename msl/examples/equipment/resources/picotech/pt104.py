"""
Example showing how to communicate with a PT-104 Data Logger from Pico Technology.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import sys
    import time

    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

    record = EquipmentRecord(
        manufacturer='PicoTech',
        model='PT-104',
        serial='GQ840/132',  # change for your device
        connection=ConnectionRecord(
            address='SDK::usbpt104',
            backend=Backend.MSL,
            properties=dict(
                ip_address='192.168.1.201:1234',  # change for your device
                open_via_ip=False,  # optional
            )
        )
    )

    # ensure that the PicoTech DLLs are available on PATH
    sys.path.append(r'C:\Program Files\Pico Technology\SDK\lib')

    # connect to the PT-104
    pt104 = record.connect()

    # get all available information about the PT-104
    info = pt104.get_unit_info()
    print(info)

    # only get the date that the PT-104 was last calibrated
    info = pt104.get_unit_info('cal_date', include_name=False)
    print('The PT-104 was last calibrated on ' + info)

    # get the IP details
    details = pt104.get_ip_details()
    print('IP details {}: '.format(details))

    # configure channel 1 to be single-ended voltage from 0 to 2.5 V
    pt104.set_channel(1, pt104.DataType.SINGLE_ENDED_TO_2500MV, 2)

    for i in range(10):
        # wait for samples to be available
        # measurement takes about 1 second per active channel
        time.sleep(1.5)

        # read the value at channel 1
        value = pt104.get_value(1)

        # for the SINGLE_ENDED_TO_2500MV configuration the scaling factor is 10 nV
        print('Loop {}, Voltage {}'.format(i, value * 10e-9))

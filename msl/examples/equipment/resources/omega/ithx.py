"""
Example showing how to communicate with an OMEGA iTHX Series Temperature and Humidity Chart Recorder.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    from msl.equipment import EquipmentRecord, ConnectionRecord, Backend

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

    omega = record.connect()
    print('T {} deg C'.format(omega.temperature()))
    print('H {}%'.format(omega.humidity()))
    print('DP {} deg F'.format(omega.dewpoint(celsius=False)))
    print('T {} deg C, H {}%'.format(*omega.temperature_humidity()))
    print('T {} deg C, H {}%, DP {} deg C'.format(*omega.temperature_humidity_dewpoint()))

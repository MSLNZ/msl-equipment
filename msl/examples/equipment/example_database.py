import os

from msl.equipment import database, connect

# this if statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    # load the database
    path = os.path.join(os.path.dirname(__file__), 'example-equipment-configuration.xml')
    dbase = database.load(path)

    # access the equipment record for each <equipment> XML element by the alias that we assigned to it
    print('Access equipment records from the alias that was assigned to the equipment...')
    print(dbase.equipment['ref'])
    print(dbase.equipment['DUT'])
    print(dbase.equipment['mono'])
    print(dbase.equipment['sensor'])
    print(dbase.equipment['adaptor'])
    print()

    # search for equipment records based on some keywords
    print('All equipment in the database manufactured by Hewlett Packard...')
    for record in dbase.records(manufacturer='H*P'):
        print(record)
    print()

    # show all of the connection records in the database
    print('All connection records in the database that use GPIB...')
    for record in dbase.connections(address='GPIB*'):
        print(repr(record))
    print()

    # get a specific equipment record (a DMM from Agilent) from the database and
    # then connect to this DMM in demo mode
    print('Connect to the DMM from Agilent with the serial number G00001...')
    dmm_record = dbase.records(manufacturer='Agilent', serial='G00001')
    print(dmm_record[0])
    dmm_ref = connect(dmm_record, 'demo')
    print(dmm_ref)
    print()

    # connect to the <equipment> XML elements that are listed in the config file
    print('Connect to the equipment in a for loop...')
    conns = {}
    for key, equip in dbase.equipment.items():
        if equip.connection is None:
            # a cable adaptor and a power sensor are listed as <equipment>
            # elements but they are not connectable items
            continue
        conns[key] = connect(equip, 'demo')
    print(conns)
    print()

    print("Ask the 'ref' DMM for its identity...")
    print(conns['ref'].query('*IDN?'))

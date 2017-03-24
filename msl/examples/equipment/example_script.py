from msl import equipment

import logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s -- %(name)s -- %(message)s")

dbase = equipment.load('example-equipment-configuration.xml')

# get a record from the example database
dmm_record = dbase.records(manufacturer='Agilent', serial="G00001")

# connect to this DMM in demo mode and send some messages to it
dmm = equipment.connect(dmm_record, True)
dmm.query('*IDN?')
dmm.query('MEASure:VOLTage:DC?')

# connect to all the <equipment> XML elements that are listed in the config file
# trying the following in non-demo mode would raise an exception for two reasons:
# 1) this equipment is (most likely) not connected to the computer running this script
# 2) some of the equipment does not have the ability to be connected to (ie. a cable adaptor
#    and a power sensor are listed as <equipment> elements but they are no connectable items)
print('Connect to all the <equipment> elements in a for loop...')
conns = equipment.connect(dbase.equipment, True)
for items in conns.items():
    print(items)
print()

# we can access each EquipmentRecord by the alias that we assigned to it
print('Access each EquipmentRecord by its alias...')
print(dbase.equipment['ref'])
print(dbase.equipment['DUT'])
print(dbase.equipment['mono'])
print(dbase.equipment['sensor'])
print(dbase.equipment['adaptor'])
print()

# connect to the Monochromator (in demo mode)
print('Connect to the Monochromator (in demo mode)...')
mono = equipment.connect(dbase.equipment['mono'], True)
print(mono)

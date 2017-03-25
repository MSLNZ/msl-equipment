import os
import logging

from msl.equipment import database

# this if statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    # set the logging configuration
    logging.basicConfig(level=logging.DEMO, format="[%(levelname)s] %(asctime)s -- %(name)s -- %(message)s")

    # load the database
    path = os.path.join(os.path.dirname(__file__), 'example-equipment-configuration.xml')
    dbase = database.load(path)

    # get a specific equipment record (a DMM from Agilent) from the database and
    # then connect to this DMM in demo mode to send some messages to it
    dmm_record = dbase.records(manufacturer='Agilent', serial="G00001")[0]
    dmm = dmm_record.connect(demo=True)
    dmm.query('*IDN?')
    dmm.query('MEASure:VOLTage:DC?')

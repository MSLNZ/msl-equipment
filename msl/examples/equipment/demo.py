import os
import logging

from msl.examples.equipment import EXAMPLES_DIR
from msl.equipment import config, connect

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':

    # set the logging configuration
    logging.basicConfig(level=logging.DEMO, format="[%(levelname)s] %(asctime)s -- %(name)s -- %(message)s")

    # load the database
    dbase = config.load(os.path.join(EXAMPLES_DIR, 'equipment-configuration.xml'))

    # get a specific equipment record (a DMM from Agilent) from the database and
    # then connect to this DMM in demo mode to send some messages to it
    dmm_record = dbase.records(manufacturer='Agilent', serial="G00001")
    dmm = connect(dmm_record, demo=True)
    dmm.query('*IDN?')
    dmm.query('MEASure:VOLTage:DC?')

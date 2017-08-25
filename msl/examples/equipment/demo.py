"""
Example showing how to open a connection in demo mode.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    import os
    import logging

    from msl.equipment import Config
    from msl.examples.equipment import EXAMPLES_DIR

    # set the logging configuration
    logging.basicConfig(level=logging.DEMO, format="[%(levelname)s] %(asctime)s -- %(name)s -- %(message)s")

    # load the database
    cfg = Config(os.path.join(EXAMPLES_DIR, 'equipment-configuration.xml'))
    dbase = cfg.database()

    # get a specific equipment record (a DMM from Agilent) from the database and
    # then connect to this DMM in demo mode to send some messages to it
    dmm_record = dbase.records(manufacturer='Agilent', serial="G00001")
    dmm = dmm_record.connect(demo=True)  # indirectly uses the factory function to connect to the equipment
    dmm.query('*IDN?')
    dmm.query('MEASure:VOLTage:DC?')

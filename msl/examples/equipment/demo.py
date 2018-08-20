"""
Example showing how to open a connection in demo mode.
"""

# this "if" statement is used so that Sphinx does not execute this script when the docs are being built
if __name__ == '__main__':
    from msl.equipment import Config
    from msl.examples.equipment import EXAMPLES_DIR

    # load the database
    cfg = Config(EXAMPLES_DIR + '/example2.xml')
    dbase = cfg.database()

    # get a specific equipment record (a DMM from Agilent) from the database and
    # then connect to this DMM in demo mode to send some messages to it
    dmm_record = dbase.records(manufacturer='Agilent', serial="537179")[0]
    dmm = dmm_record.connect(demo=True)
    print(dmm.query('*IDN?'))

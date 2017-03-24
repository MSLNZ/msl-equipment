
from msl.equipment.connection import Connection


class ConnectionMSL(Connection):

    def __init__(self, equipment_record):
        Connection.__init__(self, equipment_record)

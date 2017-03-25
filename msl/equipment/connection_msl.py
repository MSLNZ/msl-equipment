"""
Use MSL resources to establish a connection to the equipment.
"""
import logging

from msl.equipment.connection import Connection

logger = logging.getLogger(__name__)


class ConnectionMSL(Connection):

    def __init__(self, record):
        """
        Use MSL resources to establish a connection to the equipment.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`EquipmentRecord.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.

        The :data:`EquipmentRecord.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>` to use this
        class for the communication system.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An
                equipment record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        Connection.__init__(self, record)

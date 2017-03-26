"""
Base class for establishing a connection to the equipment.
"""
import time
import logging

logger = logging.getLogger(__name__)


class Connection(object):

    _backend = None

    def __init__(self, record):
        """
        All Connection :class:`~msl.equipment.constants.Backend` classes must 
        have this class as the base class.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.

        Args:
            record (:class:`~.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~.database.Database`.
        """
        self._record = record

    def read(self):
        """
        Read (receive) a response from the equipment.

        Returns:
            :py:class:`str`: The response from the equipment.
        """
        raise NotImplementedError

    receive = read

    def write(self, message):
        """
        Write (send) a message to the equipment.

        Args:
            message (str): The message to write (send) to the equipment.

        Returns:
            :py:class:`int`: The number of bytes written.
        """
        raise NotImplementedError

    send = write

    def query(self, message, delay=0.0):
        """
        Convenience method for performing a :meth:`.write` followed by a 
        :meth:`.read`.

        Args:
            message (str): The message to write (send) to the equipment.
            delay (float): The delay in seconds to wait between :meth:`.write` 
                and :meth:`.read` operations.

        Returns:
            :py:class:`str`: The response from the equipment.
        """
        logger.debug('query: ' + message)
        self.write(message)
        if delay > 0.0:
            time.sleep(delay)
        return self.read()

    ask = query

    def disconnect(self):
        """
        Implement tasks that need to be performed in order to safely disconnect 
        from the equipment. For example,

        * clean up system resources from memory
        * configure the equipment to be in a state that is safe for people 
          working in the lab when the equipment is not in use
        
        .. note::
           This method gets called automatically when the :class:`.Connection` 
           object gets destroyed.
        """
        pass

    @property
    def record(self):
        """
        :py:class:`~msl.equipment.record_types.EquipmentRecord`: The equipment record from a database.
        """
        return self._record

    @property
    def backend(self):
        """
        A reference to the software :class:`~msl.equipment.constants.Backend` class that is
        being used to communicate with the equipment.

        For example, if the backend is :data:`~msl.equipment.constants.Backend.PyVISA` then
        a Resource_ class is returned. If the backend is :data:`~msl.equipment.constants.Backend.MSL`
        then :py:data:`None` is returned (because :data:`~msl.equipment.constants.Backend.MSL` is
        not considered a backend but rather the MSL implementation of a :class:`Connection`).

        .. _Resource: http://pyvisa.readthedocs.io/en/stable/api/resources.html#pyvisa.resources.Resource
        """
        return self._backend

    def __repr__(self):
        return '{}<{}|{}|{} at {}>'.format(self.__class__.__name__,
                                           self._record.manufacturer,
                                           self._record.model,
                                           self._record.serial,
                                           self._record.connection.address)

    def __del__(self):
        self.disconnect()

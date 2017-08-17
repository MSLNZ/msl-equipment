"""
Base class for establishing a connection to the equipment.
"""
import logging
from enum import Enum

from msl.equipment.record_types import EquipmentRecord
from msl.equipment.exceptions import MSLConnectionError

logger = logging.getLogger(__name__)


class Connection(object):

    def __init__(self, record):
        """All :class:`~msl.equipment.constants.Backend` Connection classes 
        must have this class as the base class.

        Do not instantiate this class directly. Use the factory method, 
        :obj:`msl.equipment.factory.connect`, or the `record` object itself, 
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>`,
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register** 
            :class:`~.database.Database`.
        """
        if not isinstance(record, EquipmentRecord):
            raise TypeError('Must pass in an {} object'.format(EquipmentRecord.__name__))
        self._record = record

    @property
    def equipment_record(self):
        """:class:`~.record_types.EquipmentRecord`: The equipment record, from an 
        **Equipment-Register** :class:`~.database.Database`, that is being used 
        to establish the connection.
        """
        return self._record

    def disconnect(self):
        """Disconnect from the equipment.
        
        This method should be overridden in the :class:`Connection` subclass if the 
        subclass must implement tasks that need to be performed in order to safely 
        disconnect from the equipment. 
        
        For example:

            * to clean up system resources from memory (e.g., if using a manufacturer's SDK)
            * to configure the equipment to be in a state that is safe for people 
              working in the lab when the equipment is not in use
        
        Note
        ----
        This method gets called automatically when the :class:`.Connection` 
        object gets destroyed.
        """
        pass

    def __repr__(self):
        return '{}<{}|{}|{} at {}>'.format(self.__class__.__name__,
                                           self.equipment_record.manufacturer,
                                           self.equipment_record.model,
                                           self.equipment_record.serial,
                                           self.equipment_record.connection.address)

    def __del__(self):
        self.disconnect()

    def raise_exception(self, msg):
        """Raise a :exc:`ConnectionError` exception.
        
        Parameters
        ----------
        msg : :obj:`str`
            The message to display when the exception is raised.
        """
        r = self.equipment_record
        caller = '{}<{}|{}|{}>\n'.format(self.__class__.__name__, r.manufacturer, r.model, r.serial)
        raise MSLConnectionError(caller + msg)

    @staticmethod
    def convert_to_enum(item, enum, prefix='', to_upper=False):
        """Convert `item` to an `enum` value.
        
        Parameters
        ----------
        item : :obj:`int`, :obj:`float` or :obj:`str`
            If :obj:`str` then the **name** of a `enum` member.
            If :obj:`int` or :obj:`float` then the **value** of a `enum` member.
            
        enum : :obj:`~enum.Enum`
            An enum object to cast the `item`.
        
        prefix : :obj:`str`, optional
            If `item` is a :obj:`str`, then `prefix` is included at the 
            beginning of `item` before converting `item` to an `enum` value.
            
        to_upper : :obj:`bool`, optional
            If `item` is a :obj:`str`, then whether to change `item` to 
            be upper case before converting `item` to an `enum` value.

        Returns
        -------
        :obj:`~enum.Enum`
            The `enum` value.
        
        Raises
        ------
        TypeError
            If `item` is not an :obj:`int`, :obj:`float` or :obj:`str`.
        ValueError
            If `item` is not in `enum`.
        """
        if isinstance(item, Enum):
            return item

        if isinstance(item, (int, float)):
            try:
                return enum(item)
            except ValueError:
                pass

            msg = 'Invalid value {} in {}. Allowed values are: {}'.format(item, enum, [e.value for e in enum])
            Connection.log_error(msg)
            raise ValueError(msg)

        if not isinstance(item, str):
            msg = 'The item must either be an enum member name (as a string) or an enum value (as an integer/float)'
            Connection.log_error(msg)
            raise TypeError('{} -> {}. Got {} as a {}'.format(enum, msg, item, type(item)))

        member = item.replace(' ', '_')

        if to_upper:
            member = member.upper()

        if prefix and not member.startswith(prefix):
            member = prefix + member

        try:
            return enum[member]
        except KeyError:
            pass

        msg = "Invalid name '{}' in {}. Allowed names are: {}".format(member, enum, list(enum.__members__))
        Connection.log_error(msg)
        raise ValueError(msg)

    @staticmethod
    def log_debug(msg, *args, **kwargs):
        """Log a :obj:`~logging.Logger.debug` message.
        
        Parameters
        ----------
        msg : :obj:`str`
            The debug message to log.        
        """
        logger.debug(msg, *args, **kwargs)

    @staticmethod
    def log_info(msg, *args, **kwargs):
        """Log an :obj:`~logging.Logger.info` message.

        Parameters
        ----------
        msg : :obj:`str`
            The info message to log.
        """
        logger.info(msg, *args, **kwargs)

    @staticmethod
    def log_warning(msg, *args, **kwargs):
        """Log a :obj:`~logging.Logger.warning` message.

        Parameters
        ----------
        msg : :obj:`str`
            The warning message to log.
        """
        logger.warning(msg, *args, **kwargs)

    @staticmethod
    def log_error(msg, *args, **kwargs):
        """Log an :obj:`~logging.Logger.error` message.

        Parameters
        ----------
        msg : :obj:`str`
            The error message to log.
        """
        logger.error(msg, *args, **kwargs)

    @staticmethod
    def log_critical(msg, *args, **kwargs):
        """Log a :obj:`~logging.Logger.critical` message.

        Parameters
        ----------
        msg : :obj:`str`
            The critical message to log.
        """
        logger.critical(msg, *args, **kwargs)

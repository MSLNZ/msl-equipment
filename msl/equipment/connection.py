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
        """Base class for establishing a connection to the equipment.

        Do not instantiate this class directly. Use the
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>` method
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        if not isinstance(record, EquipmentRecord):
            raise TypeError('Must pass in an {} object'.format(EquipmentRecord.__name__))
        self._record = record
        self._exception_handler = MSLConnectionError

    @property
    def equipment_record(self):
        """:class:`~.record_types.EquipmentRecord`: The record that is being used for the connection.
        """
        return self._record

    def disconnect(self):
        """Disconnect from the equipment.
        
        This method should be overridden in the subclass if the subclass must implement tasks
        that need to be performed in order to safely disconnect from the equipment.
        
        For example:

            * to clean up system resources from memory (e.g., if using a manufacturer's SDK)
            * to configure the equipment to be in a state that is safe for people 
              working in the lab when the equipment is not in use
        
        Note
        ----
        This method gets called automatically when the :class:`.Connection` object gets destroyed.
        """
        pass

    def __repr__(self):
        return u'{}<{}|{}|{} at {}>'.format(
            self.__class__.__name__,
            self.equipment_record.manufacturer,
            self.equipment_record.model,
            self.equipment_record.serial,
            self.equipment_record.connection.address if self.equipment_record.connection else 'None'
        )

    def __str__(self):
        return u'{}<{}|{}|{}>'.format(
            self.__class__.__name__,
            self.equipment_record.manufacturer,
            self.equipment_record.model,
            self.equipment_record.serial
        )

    def __del__(self):
        self.disconnect()

    def raise_exception(self, msg):
        """Raise a :exc:`~.exceptions.MSLConnectionError`.
        
        Parameters
        ----------
        msg : :obj:`str`
            The message to display when the exception is raised.
        """
        self.log_error('{!r} {}'.format(self, msg))
        raise self._exception_handler('{!r}\n{}'.format(self, msg))

    @staticmethod
    def convert_to_enum(item, enum, prefix='', to_upper=False):
        """Convert `item` to an `enum` value.
        
        Parameters
        ----------
        item : :obj:`int`, :obj:`float` or :obj:`str`
            If :obj:`str` then the **name** of an `enum` member.
            If :obj:`int` or :obj:`float` then the **value** of an `enum` member.
            
        enum : :obj:`~enum.Enum`
            An enum object to cast the `item` to.
        
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
        ValueError
            If `item` is not in `enum`.
        TypeError
            If `item` is not an :obj:`int`, :obj:`float` or :obj:`str`.
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

    def set_exception_class(self, handler):
        """Set the exception-handler class for this connection.

        Parameters
        ----------
        handler : :class:`~.exceptions.MSLConnectionError`
            A subclass of :class:`~.exceptions.MSLConnectionError`

        Raises
        ------
        TypeError:
            If the `handler` is not a subclass of :class:`~.exceptions.MSLConnectionError`
        """
        if issubclass(handler, MSLConnectionError):
            self._exception_handler = handler
        else:
            raise TypeError('The exception handler must be a subclass of {}'.format(MSLConnectionError))

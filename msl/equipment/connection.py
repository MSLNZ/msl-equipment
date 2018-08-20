"""
Base class for establishing a connection to the equipment.
"""
import logging
from enum import Enum

from .record_types import EquipmentRecord
from .exceptions import MSLConnectionError

logger = logging.getLogger(__name__)


class Connection(object):

    def __init__(self, record):
        """Base class for establishing a connection to the equipment.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        if not isinstance(record, EquipmentRecord):
            raise TypeError('Must pass in an {} object'.format(EquipmentRecord.__name__))
        self._record = record
        self._exception_handler = MSLConnectionError

    @property
    def equipment_record(self):
        """:class:`.EquipmentRecord`: The information about the equipment.
        """
        return self._record

    def disconnect(self):
        """Disconnect from the equipment.
        
        This method should be overridden in the subclass if the subclass must implement
        tasks that need to be performed in order to safely disconnect from the equipment.
        
        For example:

            * to clean up system resources from memory (e.g., if using a manufacturer's SDK)
            * to configure the equipment to be in a state that is safe for people 
              working in the lab when the equipment is not in use
        
        Note
        ----
        This method gets called automatically when the :class:`.Connection` object
        gets garbage collected, which happens when the reference count is 0.
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
        """Raise a :exc:`~.MSLConnectionError`.
        
        Parameters
        ----------
        msg : :class:`str`
            The message to display when the exception is raised.
        """
        self.log_error('{!r} {}'.format(self, msg))
        raise self._exception_handler('{!r}\n{}'.format(self, msg))

    @staticmethod
    def convert_to_enum(item, enum, prefix='', to_upper=False):
        """Convert `item` to an `enum` value.
        
        Parameters
        ----------
        item : :class:`int`, :class:`float` or :class:`str`
            If :class:`str` then the **name** of an `enum` member.
            If :class:`int` or :class:`float` then the **value** of an `enum` member.
        enum : :class:`~enum.Enum`
            An enum object to cast the `item` to.
        prefix : :class:`str`, optional
            If `item` is a :class:`str`, then ensures that `prefix` is included at
            the beginning of `item` before converting `item` to an `enum` value.
        to_upper : :class:`bool`, optional
            If `item` is a :class:`str`, then whether to change `item` to
            be upper case before converting `item` to an `enum` value.

        Returns
        -------
        :class:`~enum.Enum`
            The `enum` value.
        
        Raises
        ------
        ValueError
            If `item` is not in `enum`.
        TypeError
            If `item` is not an :class:`int`, :class:`float` or :class:`str`.
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
        """Log a debug message.

        All input parameters are passed to :meth:`~logging.Logger.debug`.
        """
        logger.debug(msg, *args, **kwargs)

    @staticmethod
    def log_info(msg, *args, **kwargs):
        """Log an info message.

        All input parameters are passed to :meth:`~logging.Logger.info`.
        """
        logger.info(msg, *args, **kwargs)

    @staticmethod
    def log_warning(msg, *args, **kwargs):
        """Log a warning message.

        All input parameters are passed to :meth:`~logging.Logger.warning`.
        """
        logger.warning(msg, *args, **kwargs)

    @staticmethod
    def log_error(msg, *args, **kwargs):
        """Log an error message.

        All input parameters are passed to :meth:`~logging.Logger.error`.
        """
        logger.error(msg, *args, **kwargs)

    @staticmethod
    def log_critical(msg, *args, **kwargs):
        """Log a critical message.

        All input parameters are passed to :meth:`~logging.Logger.critical`.
        """
        logger.critical(msg, *args, **kwargs)

    def set_exception_class(self, handler):
        """Set the exception-handler class for this :class:`Connection`.

        Parameters
        ----------
        handler : :class:`~.MSLConnectionError`
            A subclass of :class:`~.MSLConnectionError`

        Raises
        ------
        TypeError
            If the `handler` is not a subclass of :class:`~.MSLConnectionError`
        """
        if issubclass(handler, MSLConnectionError):
            self._exception_handler = handler
        else:
            raise TypeError('The exception handler must be a subclass of {}'.format(MSLConnectionError))

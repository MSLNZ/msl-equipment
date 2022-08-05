"""
Base class for establishing a connection to the equipment.
"""
from __future__ import unicode_literals

from .exceptions import MSLConnectionError
from .utils import (
    logger,
    convert_to_enum
)


class Connection(object):

    def __init__(self, record):
        """Base class for establishing a connection to the equipment.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        self._record = record
        self._exception_handler = MSLConnectionError
        self._repr = '{}<{}|{}|{} at {}>'.format(
            self.__class__.__name__,
            self.equipment_record.manufacturer,
            self.equipment_record.model,
            self.equipment_record.serial,
            self.equipment_record.connection.address if self.equipment_record.connection else 'None'
        )
        self._str = '{}<{}|{}|{}>'.format(
            self.__class__.__name__,
            self.equipment_record.manufacturer,
            self.equipment_record.model,
            self.equipment_record.serial
        )

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
        return self._repr

    def __str__(self):
        return self._str

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def raise_exception(self, message):
        """Raise an :exc:`~.MSLConnectionError` and log the error message.

        Parameters
        ----------
        message : :class:`str` or :exc:`Exception`
            The message to display in the exception class that was set by
            :meth:`.set_exception_class`. If an :exc:`Exception` object then
            its string representation is used as the message.
        """
        self.log_error('%r %s', self, message)
        raise self._exception_handler('{!r}\n{}'.format(self, message))

    @staticmethod
    def convert_to_enum(obj, enum, prefix=None, to_upper=False, strict=True):
        """Convert `obj` to an Enum.

        Parameters
        ----------
        obj
            Any object to be converted to the specified `enum`. Can be a
            value of member of the specified `enum`.
        enum
            The :class:`~enum.Enum` object that `obj` should be converted to.
        prefix : :class:`str`, optional
            If `obj` is a :class:`str`, then ensures that `prefix` is included at
            the beginning of `obj` before converting `obj` to the `enum`.
        to_upper : :class:`bool`, optional
            If `obj` is a :class:`str`, then whether to change `obj` to
            be upper case before converting `obj` to the `enum`.
        strict : :class:`bool`, optional
            Whether errors should be raised. If :data:`False` and `obj` cannot
            be converted to `enum` then `obj` is returned and the error is
            logged.

        Returns
        -------
        :class:`~enum.Enum`
            The `enum`.

        Raises
        ------
        ValueError
            If `obj` is not in `enum` and `strict` is :data:`True`.
        """
        return convert_to_enum(obj, enum, prefix=prefix, to_upper=to_upper, strict=strict)

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

    @staticmethod
    def parse_address(address):
        """Determine whether a subclass should be used to connect to the equipment.

        .. attention::
           The subclass should override this method.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.

        Returns
        -------
        :class:`dict` or :data:`None`
            If the `address` is in a valid format for the subclass to be able to connect
            to the equipment then a :class:`dict` is returned containing the information
            necessary to connect to the equipment. Otherwise, if the `address` is not
            valid for the subclass to be able to connect to the equipment then
            :data:`None` is returned.
        """
        return

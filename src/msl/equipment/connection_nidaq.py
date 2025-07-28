"""
Uses NI-DAQ_ as the backend to communicate with the equipment.

.. _NI-DAQ: https://nidaqmx-python.readthedocs.io/en/stable/index.html
"""
from __future__ import annotations

try:
    import nidaqmx
    import nidaqmx.stream_readers as stream_readers
    import nidaqmx.stream_writers as stream_writers
except ImportError:
    nidaqmx = None
    stream_readers = None
    stream_writers = None

from .connection import Connection


class ConnectionNIDAQ(Connection):

    def __init__(self, record):
        """Uses NI-DAQ_ to establish a connection to the equipment.

        See the `nidaqmx examples`_ for how to use NI-DAQ_.

        The returned object from the :meth:`~.EquipmentRecord.connect` method
        is equivalent to importing the NI-DAQ_ package.

        For example::

           nidaqmx = record.connect()
           with nidaqmx.Task() as task:
               task.ai_channels.add_ai_voltage_chan('Dev1/ai0')
               voltage = task.read()

        is equivalent to::

           import nidaqmx
           with nidaqmx.Task() as task:
               task.ai_channels.add_ai_voltage_chan('Dev1/ai0')
               voltage = task.read()

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.NIDAQ`
        to use this class for the communication system. This is achieved by setting the
        value in the **Backend** field for a connection record in the :ref:`connections-database`
        to be ``NIDAQ``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        .. _nidaqmx examples: https://github.com/ni/nidaqmx-python/tree/master/nidaqmx_examples

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(ConnectionNIDAQ, self).__init__(record)

        if nidaqmx is None:
            self.raise_exception('nidaqmx is not installed. Run: pip install nidaqmx')

        try:
            self._version = nidaqmx.system.System.local().driver_version
        except OSError:
            self.raise_exception(
                'nidaqmx requires NI-DAQmx or NI-DAQmx Runtime.\n'
                'Visit https://www.ni.com/downloads/ to download the latest version of NI-DAQmx.'
            )

    @property
    def constants(self):
        """Returns the :mod:`nidaqmx.constants` module."""
        return nidaqmx.constants

    @property
    def CtrFreq(self):
        """Returns the :class:`CtrFreq <nidaqmx.types.CtrFreq>` class."""
        return nidaqmx.CtrFreq

    @property
    def CtrTick(self):
        """Returns the :class:`CtrTick <nidaqmx.types.CtrTick>` class."""
        return nidaqmx.CtrTick

    @property
    def CtrTime(self):
        """Returns the :class:`CtrTime <nidaqmx.types.CtrTime>` class."""
        return nidaqmx.CtrTime

    @property
    def DaqError(self):
        """Returns the :class:`DaqError <nidaqmx.errors.DaqError>` class."""
        return nidaqmx.DaqError

    @property
    def DaqResourceWarning(self):
        """Returns the :obj:`DaqResourceWarning <nidaqmx.errors.DaqResourceWarning>` class."""
        return nidaqmx.DaqResourceWarning

    @property
    def DaqWarning(self):
        """Returns the :class:`DaqWarning <nidaqmx.errors.DaqWarning>` class."""
        return nidaqmx.DaqWarning

    @property
    def errors(self):
        """Returns the :mod:`nidaqmx.errors` module."""
        return nidaqmx.errors

    @property
    def Scale(self):
        """Returns the :class:`Scale <nidaqmx.scale.Scale>` class."""
        return nidaqmx.Scale

    @property
    def stream_readers(self):
        """Returns the :mod:`nidaqmx.stream_readers` module."""
        return stream_readers

    @property
    def stream_writers(self):
        """Returns the :mod:`nidaqmx.stream_writers` module."""
        return stream_writers

    @property
    def system(self):
        """Returns the :mod:`nidaqmx.system` module."""
        return nidaqmx.system

    @property
    def Task(self):
        """Returns the :class:`Task <nidaqmx.task.Task>` class."""
        return nidaqmx.Task

    @property
    def types(self):
        """Returns the :mod:`nidaqmx.types` module."""
        return nidaqmx.types

    @property
    def utils(self):
        """Returns the :mod:`nidaqmx.utils` module."""
        return nidaqmx.utils

    @property
    def version(self):
        """:class:`str`: The NI-DAQmx driver version number."""
        return self._version

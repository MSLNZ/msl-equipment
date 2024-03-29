"""
Contains the information about a PicoScope channel.
"""
from __future__ import annotations

import numpy as np


class PicoScopeChannel(object):

    def __init__(self, channel, enabled, coupling, voltage_range, voltage_offset,
                 bandwidth, max_adu_value):
        """Contains the information about a PicoScope channel.
        
        This class is used by :class:`~.picoscope.PicoScope` and is not meant to be
        called directly.
        
        Parameters
        ----------
        channel : :class:`enum.IntEnum`
            The ``PSX000xChannel`` enum.
        enabled : :class:`bool`
            Whether the channel is enabled.
        coupling : :class:`enum.IntEnum`
            The ``PSX000xCoupling`` enum, e.g. AC or DC.
        voltage_range : :class:`float`
            The voltage range, in Volts.
        voltage_offset : :class:`float`
            The voltage offset, in Volts.
        bandwidth : :class:`enum.IntEnum` or :data:`None`
            The ``PSX000xBandwidthLimiter`` enum.
        max_adu_value : :class:`int`
            The maximum analog-to-digital unit.
        """
        self._channel = channel
        self._enabled = enabled
        self._coupling = coupling
        self._voltage_range = voltage_range
        self._voltage_offset = voltage_offset
        self._bandwidth = bandwidth
        self._volts_per_adu = voltage_range/float(max_adu_value)

        # the raw data in analog-to-digital units
        self._adu_values = np.empty((0, 0), dtype=np.int16)
        self._num_captures = 0
        self._num_samples = 0

    @property
    def channel(self):
        """:class:`enum.IntEnum`: The ``PSX000xChannel`` enum."""
        return self._channel

    @property
    def enabled(self):
        """:class:`bool`: Whether the channel is enabled."""
        return self._enabled

    @property
    def coupling(self):
        """:class:`enum.IntEnum`: The ``PSX000xCoupling`` enum, e.g. AC or DC."""
        return self._coupling

    @property
    def voltage_range(self):
        """:class:`float`: The voltage range, in Volts."""
        return self._voltage_range

    @property
    def voltage_offset(self):
        """:class:`float`: The voltage offset, in Volts."""
        return self._voltage_offset

    @property
    def bandwidth(self):
        """ :class:`enum.IntEnum` or :data:`None`: The ``PSX000xBandwidthLimiter`` enum."""
        return self._bandwidth

    @property
    def volts_per_adu(self):
        """:class:`float`: The conversion factor to convert ADU to volts"""
        return self._volts_per_adu

    @property
    def raw(self):
        """:class:`numpy.ndarray`: The raw data, in ADU"""
        return self._adu_values

    @property
    def buffer(self):
        """:class:`numpy.ndarray`: The raw data, in ADU"""
        return self._adu_values

    @property
    def volts(self):
        """:class:`numpy.ndarray`: The data, in volts"""
        # From the manual, the voltage offset gets added to the input channel before digitization.
        # Must convert the ADU values to volts and then subtract the offset.
        return self._adu_values * self._volts_per_adu - self._voltage_offset

    @property
    def num_samples(self):
        """:class:`int`: The size of the data array."""
        return self._adu_values.size

    def allocate(self, num_captures, num_samples):
        """Allocate memory to save the data.
        
        Parameters
        ----------
        num_captures : :class:`int`
            The number of captures
        num_samples : :class:`int`
            The number of samples
        """
        if self._adu_values.size != num_captures*num_samples:
            if num_captures == 1:
                self._adu_values = np.empty(num_samples, dtype=np.int16)
            else:
                self._adu_values = np.empty((num_captures, num_samples), dtype=np.int16)

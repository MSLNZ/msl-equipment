"""
Contains the information about a PicoScope channel.
"""
import numpy as np


class PicoScopeChannel(object):

    def __init__(self, channel, enabled, coupling, voltage_range, voltage_offset,
                 bandwidth, max_adu_value):
        """Contains the information about a PicoScope channel.
        
        This class is used by :class:`.picoscope.PicoScope` and is not meant to be 
        called directly.
        
        Parameters
        ----------
        channel : :obj:`enum.IntEnum`
            The channel number.
        enabled : :obj:`bool`
            Whether the channel is enabled.
        coupling : :obj:`enum.IntEnum`
            The coupling, e.g. AC or DC. 
        voltage_range : :obj:`float`
            The voltage range, in Volts.
        voltage_offset : :obj:`float`
            The voltage offset, in Volts.
        bandwidth : :obj:`enum.IntEnum` or :obj:`None`
            The bandwidth used, if the PicoScope supports a ``BandwidthLimiter``.
        max_adu_value : :obj:`int`
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
        """:obj:`enum.IntEnum`: The channel number."""
        return self._channel

    @property
    def enabled(self):
        """:obj:`bool`: Whether the channel is enabled."""
        return self._enabled

    @property
    def coupling(self):
        """:obj:`enum.IntEnum`: The coupling, e.g. AC or DC."""
        return self._coupling

    @property
    def voltage_range(self):
        """:obj:`float`: The voltage range, in Volts."""
        return self._voltage_range

    @property
    def voltage_offset(self):
        """:obj:`float`: The voltage offset, in Volts."""
        return self._voltage_offset

    @property
    def bandwidth(self):
        """ :obj:`enum.IntEnum` or :obj:`None`: The bandwidth used, if 
        the PicoScope supports a ``BandwidthLimiter``."""
        return self._bandwidth

    @property
    def volts_per_adu(self):
        """:obj:`float`: The connversion factor to convert ADU to volts"""
        return self._volts_per_adu

    @property
    def raw(self):
        """:obj:`numpy.ndarray`: The raw data, in ADU"""
        return self._adu_values

    @property
    def buffer(self):
        """:obj:`numpy.ndarray`: The raw data, in ADU"""
        return self._adu_values

    @property
    def volts(self):
        """:obj:`numpy.ndarray`: The data, in volts"""
        # From the manual, the voltage offset gets added to the input channel before digitization.
        # Must convert the ADU values to volts and then subtract the offset.
        return self._adu_values * self._volts_per_adu - self._voltage_offset

    @property
    def num_samples(self):
        """:obj:`int`: The size of the data array."""
        return self._adu_values.size

    def allocate(self, num_captures, num_samples):
        """Allocate memory to save the data.
        
        Parameters
        ----------
        num_captures : :obj:`int`
            The number of captures
        num_samples : :obj:`int`
            The number of samples
        """
        if self._adu_values.size != num_captures*num_samples:
            if num_captures == 1:
                self._adu_values = np.empty(num_samples, dtype=np.int16)
            else:
                self._adu_values = np.empty((num_captures, num_samples), dtype=np.int16)

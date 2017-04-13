import numpy as np


class PicoScopeChannel(object):

    def __init__(self, channel, enabled, coupling, voltage_range, voltage_offset, bandwidth, max_adu_value):
        self._channel = channel
        self._enabled = enabled
        self._coupling = coupling
        self._voltage_range = voltage_range
        self._voltage_offset = voltage_offset
        self._bandwidth = bandwidth
        self._volts_per_adu = voltage_range/float(max_adu_value)
        self._adu_values = np.empty((0, 0), dtype=np.int16)  # the raw data in analog-to-digital units
        self._num_captures = 0
        self._num_samples = 0

    @property
    def channel(self):
        return self._channel

    @property
    def enabled(self):
        return self._enabled

    @property
    def coupling(self):
        return self._coupling

    @property
    def voltage_range(self):
        return self._voltage_range

    @property
    def voltage_offset(self):
        return self._voltage_offset

    @property
    def bandwidth(self):
        return self._bandwidth

    @property
    def volts_per_adu(self):
        return self._volts_per_adu

    @property
    def raw(self):
        return self._adu_values

    @property
    def buffer(self):
        return self._adu_values

    @property
    def volts(self):
        # From the manual, the voltage offset gets added to the input channel before digitization.
        # Must convert the ADU values to volts and then subtract the offset.
        return self._adu_values * self._volts_per_adu - self._voltage_offset

    @property
    def num_samples(self):
        return self._adu_values.size

    def allocate(self, num_captures, num_samples):
        if self._adu_values.size != num_captures*num_samples:
            if num_captures == 1:
                self._adu_values = np.empty(num_samples, dtype=np.int16)
            else:
                self._adu_values = np.empty((num_captures, num_samples), dtype=np.int16)

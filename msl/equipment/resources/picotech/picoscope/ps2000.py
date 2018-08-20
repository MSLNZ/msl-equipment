"""
A wrapper around the PicoScope ps2000 SDK.
"""
from ctypes import c_uint8, byref

from msl.equipment.resources import register
from .picoscope_2k3k import PicoScope2k3k
from .functions import ps2000_funcptrs


@register(manufacturer='Pico\s*Tech', model='2[12]0[2345]A*(?<!MSO)$')
class PicoScope2000(PicoScope2k3k):

    FIRST_USB = 1
    LAST_USB = 127
    MAX_UNITS = (LAST_USB - FIRST_USB + 1)
    MAX_TIMEBASE = 19
    PS2105_MAX_TIMEBASE = 20
    PS2104_MAX_TIMEBASE = 19
    PS2200_MAX_TIMEBASE = 23
    MAX_OVERSAMPLE = 256
    PS2105_MAX_ETS_CYCLES = 250
    PS2105_MAX_ETS_INTERLEAVE = 50
    PS2104_MAX_ETS_CYCLES = 125
    PS2104_MAX_ETS_INTERLEAVE = 25
    PS2203_MAX_ETS_CYCLES = 250
    PS2203_MAX_ETS_INTERLEAVE = 50
    PS2204_MAX_ETS_CYCLES = 250
    PS2204_MAX_ETS_INTERLEAVE = 40
    PS2205_MAX_ETS_CYCLES = 250
    PS2205_MAX_ETS_INTERLEAVE = 40
    MIN_ETS_CYCLES_INTERLEAVE_RATIO = 1
    MAX_ETS_CYCLES_INTERLEAVE_RATIO = 10
    MIN_SIGGEN_FREQ = 0.0
    MAX_SIGGEN_FREQ = 100000.0
    MAX_VALUE = 32767
    MIN_VALUE = -32767
    LOST_DATA = -32768

    # EXT_MAX_VOLTAGE = ?

    def __init__(self, record):
        """A wrapper around the PicoScope ps2000 SDK.
        
        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(PicoScope2000, self).__init__(record, ps2000_funcptrs)

    def last_button_press(self):
        """
        This function returns the last registered state of the pushbutton on the PicoScope
        2104 or 2105 PC Oscilloscope and then resets the status to zero.
        """
        return self.sdk.ps2000_last_button_press(self._handle)

    def set_led(self, state):
        """
        This function turns the LED on the oscilloscope on and off, and controls its colour.
        """
        return self.sdk.ps2000_set_led(self._handle, state)

    def set_light(self, state):
        """
        This function controls the white light that illuminates the probe tip on a handheld
        oscilloscope.
        """
        return self.sdk.ps2000_set_light(self._handle, state)

    def set_sig_gen_arbitrary(self, offset_voltage, pk_to_pk, start_delta_phase, stop_delta_phase,
                              delta_phase_increment, dwell_count, arbitrary_waveform_size, sweep_type, sweeps):
        """
        This function programs the signal generator to produce an arbitrary waveform.
        """
        arbitrary_waveform = c_uint8()
        ret = self.sdk.ps2000_set_sig_gen_arbitrary(self._handle, offset_voltage, pk_to_pk, start_delta_phase,
                                                    stop_delta_phase, delta_phase_increment, dwell_count,
                                                    byref(arbitrary_waveform), arbitrary_waveform_size,
                                                    sweep_type, sweeps)
        return ret.value, arbitrary_waveform.value

    def set_sig_gen_built_in(self, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency,
                             increment, dwell_time, sweep_type, sweeps):
        """
        This function sets up the signal generator to produce a signal from a list of built-in
        waveforms. If different start and stop frequencies are specified, the oscilloscope will
        sweep either up, down or up and down.
        """
        return self.sdk.ps2000_set_sig_gen_built_in(self._handle, offset_voltage, pk_to_pk, wave_type,
                                                    start_frequency, stop_frequency, increment, dwell_time,
                                                    sweep_type, sweeps)

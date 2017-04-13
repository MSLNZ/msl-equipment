from ctypes import c_uint8, byref

from .picoscope_2k3k import PicoScope2k3k
from .functions import ps2000_funcptrs
from .structs import (
    PS2000TriggerChannelProperties,
    PS2000TriggerConditions,
    PS2000PwqConditions
)


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

    def __init__(self, record):
        """
        A wrapper around the PicoScope ps2000 SDK.
        
        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        PicoScope2k3k.__init__(self, record, ps2000_funcptrs)

    def last_button_press(self):
        """
        This function returns the last registered state of the pushbutton on the PicoScope
        2104 or 2105 PC Oscilloscope and then resets the status to zero.
        """
        return self.sdk.ps2000_last_button_press(self._handle)

    def set_adv_trigger_channel_conditions(self, n_conditions):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is defined by
        a :class:`~.picoscope_structs.PS2000TriggerConditions` structure.
        """
        conditions = PS2000TriggerConditions()
        ret = self.sdk.ps2000SetAdvTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return ret.value, conditions.value  # TODO return struct values

    def set_adv_trigger_channel_properties(self, n_channel_properties, auto_trigger_milliseconds):
        """
        This function is used to enable or disable triggering and set its parameters. 
        
        Populates the :class:`~.picoscope_structs.PS2000TriggerChannelProperties` structure.
        """
        channel_properties = PS2000TriggerChannelProperties()
        ret = self.sdk.ps2000SetAdvTriggerChannelProperties(self._handle, byref(channel_properties),
                                                            n_channel_properties, auto_trigger_milliseconds)
        return ret.value, channel_properties.value  # TODO return struct values

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

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, pulse_width_type):
        """
        This function sets up pulse width qualification, which can be used on its own for pulse
        width triggering or combined with other triggering to produce more complex triggers.
        The pulse width qualifier is set by defining a :class:`~.picoscope_structs.PS2000PwqConditions`
        structure.
        """
        conditions = PS2000PwqConditions()
        ret = self.sdk.ps2000SetPulseWidthQualifier(self._handle, byref(conditions), n_conditions, direction,
                                                    lower, upper, pulse_width_type)
        return ret.value, conditions.value  # TODO return struct values

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

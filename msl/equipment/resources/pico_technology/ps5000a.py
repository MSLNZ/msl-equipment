from ctypes import byref

from .error_codes import c_enum
from .picoscope_api import PicoScopeApi
from .picoscope_functions import ps5000aApi_funcptrs
from .picoscope_structs import (PS5000ATriggerInfo, PS5000APwqConditions,
                                PS5000ATriggerConditions, PS5000ATriggerChannelProperties)


class PicoScope5000A(PicoScopeApi):

    PS5000A_MAX_VALUE_8BIT = 32512
    PS5000A_MIN_VALUE_8BIT = -32512
    PS5000A_MAX_VALUE_16BIT = 32767
    PS5000A_MIN_VALUE_16BIT = -32767
    PS5000A_LOST_DATA = -32768
    PS5000A_EXT_MAX_VALUE = 32767
    PS5000A_EXT_MIN_VALUE = -32767
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_DELAY_COUNT = 8388607
    PS5X42A_MAX_SIG_GEN_BUFFER_SIZE = 16384
    PS5X43A_MAX_SIG_GEN_BUFFER_SIZE = 32768
    PS5X44A_MAX_SIG_GEN_BUFFER_SIZE = 49152
    MIN_SIG_GEN_BUFFER_SIZE = 1
    MIN_DWELL_COUNT = 3
    # MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    AWG_DAC_FREQUENCY = 200e6
    AWG_PHASE_ACCUMULATOR = 4294967296.0
    MAX_ANALOGUE_OFFSET_50MV_200MV = 0.250
    MIN_ANALOGUE_OFFSET_50MV_200MV = -0.250
    MAX_ANALOGUE_OFFSET_500MV_2V = 2.500
    MIN_ANALOGUE_OFFSET_500MV_2V = -2.500
    MAX_ANALOGUE_OFFSET_5V_20V = 20.
    MIN_ANALOGUE_OFFSET_5V_20V = -20.
    PS5244A_MAX_ETS_CYCLES = 500
    PS5244A_MAX_ETS_INTERLEAVE = 40
    PS5243A_MAX_ETS_CYCLES = 250
    PS5243A_MAX_ETS_INTERLEAVE = 20
    PS5242A_MAX_ETS_CYCLES = 125
    PS5242A_MAX_ETS_INTERLEAVE = 10
    PS5000A_SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN = 0xFFFFFFFF
    PS5000A_SINE_MAX_FREQUENCY = 20000000.
    PS5000A_SQUARE_MAX_FREQUENCY = 20000000.
    PS5000A_TRIANGLE_MAX_FREQUENCY = 20000000.
    PS5000A_SINC_MAX_FREQUENCY = 20000000.
    PS5000A_RAMP_MAX_FREQUENCY = 20000000.
    PS5000A_HALF_SINE_MAX_FREQUENCY = 20000000.
    PS5000A_GAUSSIAN_MAX_FREQUENCY = 20000000.
    PS5000A_MIN_FREQUENCY = 0.03

    def __init__(self, record):
        """
        A wrapper around the PicoScope ps5000a SDK.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        PicoScopeApi.__init__(self, record, ps5000aApi_funcptrs)

    def get_device_resolution(self):
        """
        This function retrieves the resolution the specified device will run in.
        """
        resolution = c_enum()
        self.sdk.ps5000aGetDeviceResolution(self._handle, byref(resolution))
        return resolution.value

    def get_trigger_info_bulk(self, from_segment_index, to_segment_index):
        """
        This function is in the header file, but it is not in the manual.

        Populates the :class:`~.picoscope_structs.PS5000ATriggerInfo` structure.
        """
        trigger_info = PS5000ATriggerInfo()
        self.sdk.ps5000aGetTriggerInfoBulk(self._handle, byref(trigger_info), from_segment_index, to_segment_index)
        return trigger_info.value  # TODO return structure values

    def set_device_resolution(self, resolution):
        """
        This function sets the new resolution. When using 12 bits or more the memory is
        halved. When using 15-bit resolution only 2 channels can be enabled to capture data,
        and when using 16-bit resolution only one channel is available. If resolution is
        changed, any data captured that has not been saved will be lost. If
        :meth:`set_channel` is not called, :meth:`run_block` and :meth:`run_streaming`
        may fail.
        """
        return self.sdk.ps5000aSetDeviceResolution(self._handle, resolution)

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, pulse_width_type):
        """
        This function sets up pulse-width qualification, which can be used on its own for pulse
        width triggering or combined with window triggering to produce more complex
        triggers. The pulse-width qualifier is set by defining one or more structures that are
        then ORed together. Each structure is itself the AND of the states of one or more of
        the inputs. This AND-OR logic allows you to create any possible Boolean function of
        the scope's inputs.

        Populates the :class:`~.picoscope_structs.PS5000APwqConditions` structure.
        """
        conditions = PS5000APwqConditions()
        self.sdk.ps5000aSetPulseWidthQualifier(self._handle, byref(conditions), n_conditions, direction, lower,
                                               upper, pulse_width_type)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_conditions(self, n_conditions):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is defined by
        one or more :class:`~.picoscope_structs.PS5000ATriggerConditions` structures that are then 
        ORed together. Each structure is itself the AND of the states of one or more of the inputs.
        This AND-OR logic allows you to create any possible Boolean function of the scope's
        inputs.
        
        If complex triggering is not required, use :meth:`set_simple_trigger`.
        """
        conditions = PS5000ATriggerConditions()
        self.sdk.ps5000aSetTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_directions(self, channel_a, channel_b, channel_c, channel_d, ext, aux):
        """
        This function sets the direction of the trigger for each channel.
        """
        return self.sdk.ps5000aSetTriggerChannelDirections(self._handle, channel_a, channel_b, channel_c,
                                                           channel_d, ext, aux)

    def set_trigger_channel_properties(self, n_channel_properties, aux_output_enable, auto_trigger_milliseconds):
        """
        This function is used to enable or disable triggering and set its parameters.

        Populates the :class:`~.picoscope_structs.PS5000ATriggerChannelProperties` structure.
        """
        channel_properties = PS5000ATriggerChannelProperties()
        self.sdk.ps5000aSetTriggerChannelProperties(self._handle, byref(channel_properties), n_channel_properties,
                                                    aux_output_enable, auto_trigger_milliseconds)
        return channel_properties.value  # TODO return structure values

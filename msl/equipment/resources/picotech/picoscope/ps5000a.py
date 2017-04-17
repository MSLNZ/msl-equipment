import math
from ctypes import byref

from .picoscope import c_enum
from .picoscope_api import PicoScopeApi
from .functions import ps5000aApi_funcptrs
from .structs import (
    PS5000ATriggerInfo,
    PS5000APwqConditions,
    PS5000ATriggerConditions,
    PS5000ATriggerChannelProperties,
)


class PicoScope5000A(PicoScopeApi):

    MAX_VALUE_8BIT = 32512
    MIN_VALUE_8BIT = -32512
    MAX_VALUE_16BIT = 32767
    MIN_VALUE_16BIT = -32767
    LOST_DATA = -32768
    EXT_MAX_VALUE = 32767
    EXT_MIN_VALUE = -32767
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_DELAY_COUNT = 8388607
    PS5X42A_MAX_SIG_GEN_BUFFER_SIZE = 16384
    PS5X43A_MAX_SIG_GEN_BUFFER_SIZE = 32768
    PS5X44A_MAX_SIG_GEN_BUFFER_SIZE = 49152
    MIN_SIG_GEN_BUFFER_SIZE = 1
    MIN_DWELL_COUNT = 3
    MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
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
    SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN = 0xFFFFFFFF
    SINE_MAX_FREQUENCY = 20000000.
    SQUARE_MAX_FREQUENCY = 20000000.
    TRIANGLE_MAX_FREQUENCY = 20000000.
    SINC_MAX_FREQUENCY = 20000000.
    RAMP_MAX_FREQUENCY = 20000000.
    HALF_SINE_MAX_FREQUENCY = 20000000.
    GAUSSIAN_MAX_FREQUENCY = 20000000.
    MIN_FREQUENCY = 0.03

    EXT_MAX_VOLTAGE = 5.0

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
        return self.enDeviceResolution(resolution.value)

    def _get_timebase_index(self, dt):
        """
        See the manual for the sample interval formula as a function of device resolution.
        """
        resolution = self.get_device_resolution()
        if resolution == self.enDeviceResolution.RES_8BIT:
            if dt < 8e-9:
                return math.log(1e9 * dt, 2)
            else:
                return 125e6 * dt + 2
        elif resolution == self.enDeviceResolution.RES_12BIT:
            if dt < 16e-9:
                return math.log(500e6 * dt, 2) + 1
            else:
                return 62.5e6 * dt + 3
        elif resolution == self.enDeviceResolution.RES_16BIT:
            return 62.5e6 * dt + 3
        else:  # 14- and 15-bit resolution
            return 125e6 * dt + 2

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
        r = self.convert_to_enum(resolution, self.enDeviceResolution, 'RES_')
        return self.sdk.ps5000aSetDeviceResolution(self._handle, r)

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

    def set_trigger_channel_properties(self, channel_properties, timeout=0.1, aux_output_enable=0):
        """
        This function is used to enable or disable triggering and set its parameters.

        Populates the :class:`~.picoscope_structs.PS5000ATriggerChannelProperties` structure.
        
        Args:
            aux_output_enable (int): Only used by ps5000.        
        """
        auto_trigger_ms = round(max(0, timeout * 1e3))
        #channel_properties = PS5000ATriggerChannelProperties()
        self.sdk.ps5000aSetTriggerChannelProperties(self._handle, byref(channel_properties), 1,
                                                    aux_output_enable, auto_trigger_ms)

        #return channel_properties  # TODO return structure values

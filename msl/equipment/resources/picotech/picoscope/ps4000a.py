"""
A wrapper around the PicoScope ps4000a SDK.
"""
from ctypes import c_int8, c_int16, c_uint16, c_int32, byref

from msl.equipment.resources import register
from .picoscope_api import PicoScopeApi
from .functions import ps4000aApi_funcptrs


@register(manufacturer='Pico\s*Tech', model='4(44|82)4')
class PicoScope4000A(PicoScopeApi):

    MAX_VALUE = 32767
    MIN_VALUE = -32767
    LOST_DATA = -32768
    EXT_MAX_VALUE = 32767
    EXT_MIN_VALUE = -32767
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_DELAY_COUNT = 8388607
    MAX_SIG_GEN_BUFFER_SIZE = 16384
    MIN_SIG_GEN_BUFFER_SIZE = 10
    MIN_DWELL_COUNT = 10
    MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    AWG_DAC_FREQUENCY = 80e6
    AWG_PHASE_ACCUMULATOR = 4294967296.0
    MAX_ANALOGUE_OFFSET_50MV_200MV = 0.250
    MIN_ANALOGUE_OFFSET_50MV_200MV = -0.250
    MAX_ANALOGUE_OFFSET_500MV_2V = 2.500
    MIN_ANALOGUE_OFFSET_500MV_2V = -2.500
    MAX_ANALOGUE_OFFSET_5V_20V = 20.
    MIN_ANALOGUE_OFFSET_5V_20V = -20.
    SINE_MAX_FREQUENCY = 1000000.
    SQUARE_MAX_FREQUENCY = 1000000.
    TRIANGLE_MAX_FREQUENCY = 1000000.
    SINC_MAX_FREQUENCY = 1000000.
    RAMP_MAX_FREQUENCY = 1000000.
    HALF_SINE_MAX_FREQUENCY = 1000000.
    GAUSSIAN_MAX_FREQUENCY = 1000000.
    MIN_FREQUENCY = 0.03

    # EXT_MAX_VOLTAGE = ?

    def __init__(self, record):
        """A wrapper around the PicoScope ps4000a SDK.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(PicoScope4000A, self).__init__(record, ps4000aApi_funcptrs)

    def apply_resistance_scaling(self, channel, range_, buffer_length):
        """
        This function is in the header file, but it is not in the manual.
        """
        buffer_max = c_int16()
        buffer_min = c_int16()
        overflow = c_int16()
        self.sdk.ps4000aApplyResistanceScaling(self._handle, channel, range_, byref(buffer_max), byref(buffer_min),
                                               buffer_length, byref(overflow))
        return buffer_max.value, buffer_min.value, overflow.value

    def connect_detect(self, sensors):
        """
        This function is in the header file, but it is not in the manual.
        """
        return self.sdk.ps4000aConnectDetect(self._handle, byref(sensors), len(sensors))

    def device_meta_data(self, meta_type, operation, format_):
        """
        This function is in the header file, but it is not in the manual.
        """
        settings = c_int8()
        n_settings_length = c_int32()
        self.sdk.ps4000aDeviceMetaData(self._handle, byref(settings), byref(n_settings_length), meta_type,
                                       operation, format_)
        return settings.value, n_settings_length.value

    def get_common_mode_overflow(self):
        """
        This function is in the header file, but it is not in the manual.
        """
        overflow = c_uint16()
        self.sdk.ps4000aGetCommonModeOverflow(self._handle, byref(overflow))
        return overflow.value

    def get_string(self, string_value):
        """
        This function is in the header file, but it is not in the manual.
        """
        string = c_int8()
        string_length = c_int32()
        self.sdk.ps4000aGetString(self._handle, string_value, byref(string), byref(string_length))
        return string.value, string_length.value

    def set_channel_led(self, led_states):
        """
        This function is in the header file, but it is not in the manual.
        """
        return self.sdk.ps4000aSetChannelLed(self._handle, byref(led_states), len(led_states))

    def set_pulse_width_qualifier_conditions(self, conditions, info):
        """
        This function sets up the conditions for pulse width qualification, which can be used on
        its own for pulse width triggering or combined with window triggering to produce more
        complex triggers. Each call to this function creates a pulse width qualifier equal to the
        logical AND of the elements of the ``conditions`` array. Calling this function multiple
        times creates the logical OR of multiple AND operations. This AND-OR logic allows you
        to create any possible Boolean function of the scope's inputs.
        
        Other settings of the pulse width qualifier are configured by calling
        :meth:`set_pulse_width_qualifier_properties`.
        """
        return self.sdk.ps4000aSetPulseWidthQualifierConditions(self._handle, byref(conditions), len(conditions), info)

    def set_pulse_width_qualifier_properties(self, direction, lower, upper, pulse_width_type):
        """
        This function configures the general properties of the pulse width qualifier.
        """
        return self.sdk.ps4000aSetPulseWidthQualifierProperties(self._handle, direction, lower,
                                                                upper, pulse_width_type)

    def set_trigger_channel_directions(self, directions):
        """
        This function sets the direction of the trigger for the specified channels.
        """
        return self.sdk.ps4000aSetTriggerChannelDirections(self._handle, byref(directions), len(directions))

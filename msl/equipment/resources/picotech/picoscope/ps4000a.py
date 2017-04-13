from ctypes import c_int8, c_int16, c_uint16, c_int32, byref

from .picoscope_api import PicoScopeApi
from .functions import ps4000aApi_funcptrs
from .structs import (
    PS4000AConnectDetect,
    PS4000AChannelLedSetting,
    PS4000ACondition,
    PS4000ADirection,
    PS4000ATriggerChannelProperties
)


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
    # MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
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
        """
        A wrapper around the PicoScope ps4000a SDK.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        PicoScopeApi.__init__(self, record, ps4000aApi_funcptrs)

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

    def connect_detect(self, n_sensors):
        """
        This function is in the header file, but it is not in the manual.
        
        Populates the :class:`~.picoscope_structs.PS4000AConnectDetect` structure.
        """
        sensor = PS4000AConnectDetect()
        self.sdk.ps4000aConnectDetect(self._handle, byref(sensor), n_sensors)
        return sensor.value  # TODO return structure values

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

    def set_channel_led(self, n_led_states):
        """
        This function is in the header file, but it is not in the manual.
        
        Populates the :class:`~.picoscope_structs.PS4000AChannelLedSetting` structure.
        """
        led_states = PS4000AChannelLedSetting()
        self.sdk.ps4000aSetChannelLed(self._handle, byref(led_states), n_led_states)
        return led_states.value  # TODO return structure values

    def set_pulse_width_qualifier_conditions(self, n_conditions, info):
        """
        This function sets up the conditions for pulse width qualification, which can be used on
        its own for pulse width triggering or combined with window triggering to produce more
        complex triggers. Each call to this function creates a pulse width qualifier equal to the
        logical AND of the elements of the ``conditions`` array. Calling this function multiple
        times creates the logical OR of multiple AND operations. This AND-OR logic allows you
        to create any possible Boolean function of the scope's inputs.
        
        Other settings of the pulse width qualifier are configured by calling
        :meth:`set_pulse_width_qualifier_properties`.

        Populates the :class:`~.picoscope_structs.PS4000ACondition` structure.
        """
        conditions = PS4000ACondition()
        self.sdk.ps4000aSetPulseWidthQualifierConditions(self._handle, byref(conditions), n_conditions, info)
        return conditions.value

    def set_pulse_width_qualifier_properties(self, direction, lower, upper, pulse_width_type):
        """
        This function configures the general properties of the pulse width qualifier.
        """
        return self.sdk.ps4000aSetPulseWidthQualifierProperties(self._handle, direction, lower,
                                                                upper, pulse_width_type)

    def set_trigger_channel_conditions(self, n_conditions, info):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is set up by
        defining an array of one or more :class:`~.picoscope_structs.PS4000ACondition` structures 
        that are then ANDed together. The function can be called multiple times, in which case the 
        trigger logic is ORed with that defined by previous calls. This AND-OR logic allows you to
        create any possible Boolean function of the scope's inputs.
        """
        conditions = PS4000ACondition()
        self.sdk.ps4000aSetTriggerChannelConditions(self._handle, byref(conditions), n_conditions, info)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_directions(self, n_directions):
        """
        This function sets the direction of the trigger for the specified channels.

        Populates the :class:`~.picoscope_structs.PS4000ADirection` structure.
        """
        directions = PS4000ADirection()
        self.sdk.ps4000aSetTriggerChannelDirections(self._handle, byref(directions), n_directions)
        return directions.value  # TODO return structure values

    def set_trigger_channel_properties(self, n_channel_properties, aux_output_enable, auto_trigger_milliseconds):
        """
        This function is used to enable or disable triggering and set its parameters.

        Populates the :class:`~.picoscope_structs.PS4000ATriggerChannelProperties` structure.
        """
        channel_properties = PS4000ATriggerChannelProperties()
        self.sdk.ps4000aSetTriggerChannelProperties(self._handle, byref(channel_properties), n_channel_properties,
                                                    aux_output_enable, auto_trigger_milliseconds)
        return channel_properties.value  # TODO return structure values

from ctypes import byref

from .picoscope_api import PicoScopeApi
from .picoscope_functions import ps2000aApi_funcptrs
from .picoscope_structs import (PS2000APwqConditions, PS2000ATriggerConditions,
                                PS2000ATriggerChannelProperties, PS2000ADigitalChannelDirections)


class PicoScope2000A(PicoScopeApi):

    PS2208_MAX_ETS_CYCLES = 500
    PS2208_MAX_INTERLEAVE = 20
    PS2207_MAX_ETS_CYCLES = 500
    PS2207_MAX_INTERLEAVE = 20
    PS2206_MAX_ETS_CYCLES = 250
    PS2206_MAX_INTERLEAVE = 10
    PS2000A_EXT_MAX_VALUE = 32767
    PS2000A_EXT_MIN_VALUE = -32767
    PS2000A_MAX_LOGIC_LEVEL = 32767
    PS2000A_MIN_LOGIC_LEVEL = -32767
    MIN_SIG_GEN_FREQ = 0.0
    MAX_SIG_GEN_FREQ = 20000000.0
    PS2000A_MAX_SIG_GEN_BUFFER_SIZE = 8192
    PS2000A_MIN_SIG_GEN_BUFFER_SIZE = 1
    PS2000A_MIN_DWELL_COUNT = 3
    # PS2000A_MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    PS2000A_MAX_ANALOGUE_OFFSET_50MV_200MV = 0.250
    PS2000A_MIN_ANALOGUE_OFFSET_50MV_200MV = -0.250
    PS2000A_MAX_ANALOGUE_OFFSET_500MV_2V = 2.500
    PS2000A_MIN_ANALOGUE_OFFSET_500MV_2V = -2.500
    PS2000A_MAX_ANALOGUE_OFFSET_5V_20V = 20.
    PS2000A_MIN_ANALOGUE_OFFSET_5V_20V = -20.
    PS2000A_SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN = 0xFFFFFFFF
    PS2000A_SINE_MAX_FREQUENCY = 1000000.
    PS2000A_SQUARE_MAX_FREQUENCY = 1000000.
    PS2000A_TRIANGLE_MAX_FREQUENCY = 1000000.
    PS2000A_SINC_MAX_FREQUENCY = 1000000.
    PS2000A_RAMP_MAX_FREQUENCY = 1000000.
    PS2000A_HALF_SINE_MAX_FREQUENCY = 1000000.
    PS2000A_GAUSSIAN_MAX_FREQUENCY = 1000000.
    PS2000A_PRBS_MAX_FREQUENCY = 1000000.
    PS2000A_PRBS_MIN_FREQUENCY = 0.03
    PS2000A_MIN_FREQUENCY = 0.03

    def __init__(self, record):
        """
        A wrapper around the PicoScope ps2000a SDK.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        PicoScopeApi.__init__(self, record, ps2000aApi_funcptrs)

    def set_digital_analog_trigger_operand(self, operand):
        """
        This function is define in the header file, but it is not in the manual.
        """
        return self.sdk.ps2000aSetDigitalAnalogTriggerOperand(self._handle, operand)

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, pulse_width_type):
        """
        This function sets up pulse-width qualification, which can be used on its own for pulsewidth
        triggering or combined with window triggering to produce more complex
        triggers. The pulse-width qualifier is set by defining one or more structures that are
        then ORed together. Each structure is itself the AND of the states of one or more of
        the inputs. This AND-OR logic allows you to create any possible Boolean function of
        the scope's inputs.
        """
        conditions = PS2000APwqConditions()
        self.sdk.ps2000aSetPulseWidthQualifier(self._handle, byref(conditions), n_conditions,
                                               direction, lower, upper, pulse_width_type)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_conditions(self, n_conditions):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is defined by
        one or more :class:`~.picoscope_structs.PS2000ATriggerConditions` structures that are then ORed
        together. Each structure is itself the AND of the states of one or more of the inputs.
        This AND-OR logic allows you to create any possible Boolean function of the scope's
        inputs.
        """
        conditions = PS2000ATriggerConditions()
        self.sdk.ps2000aSetTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_directions(self, channel_a, channel_b, channel_c, channel_d, ext, aux):
        """
        This function sets the direction of the trigger for each channel.
        """
        return self.sdk.ps2000aSetTriggerChannelDirections(self._handle, channel_a, channel_b, channel_c,
                                                           channel_d, ext, aux)

    def set_trigger_channel_properties(self, n_channel_properties, aux_output_enable, auto_trigger_milliseconds):
        """
        This function is used to enable or disable triggering and set its parameters.
        
        Populates the :class:`~.picoscope_structs.PS2000ATriggerChannelProperties` structure.
        """
        channel_properties = PS2000ATriggerChannelProperties()
        self.sdk.ps2000aSetTriggerChannelProperties(self._handle, byref(channel_properties), n_channel_properties,
                                                    aux_output_enable, auto_trigger_milliseconds)
        return channel_properties.value  # TODO return structure values

    def set_trigger_digital_port_properties(self, n_directions):
        """
        This function will set the individual Digital channels trigger directions. Each trigger
        direction consists of a channel name and a direction. If the channel is not included in
        the array of :class:`~.picoscope_structs.PS2000ADigitalChannelDirections` the driver 
        assumes the digital channel's trigger direction is ``PS2000A_DIGITAL_DONT_CARE``.
        """
        directions = PS2000ADigitalChannelDirections()
        self.sdk.ps2000aSetTriggerDigitalPortProperties(self._handle, byref(directions), n_directions)
        return directions.value  # TODO return structure values

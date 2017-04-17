from ctypes import byref

from .picoscope_api import PicoScopeApi
from .functions import ps5000Api_funcptrs
from .structs import (
    PS5000PwqConditions,
    PS5000TriggerConditions,
    PS5000TriggerChannelProperties
)


class PicoScope5000(PicoScopeApi):

    MAX_OVERSAMPLE_8BIT = 256
    MAX_VALUE = 32512
    MIN_VALUE = -32512
    LOST_DATA = -32768
    EXT_MAX_VALUE = 32767
    EXT_MIN_VALUE = -32767
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_DELAY_COUNT = 8388607
    MAX_SIG_GEN_BUFFER_SIZE = 8192
    MIN_SIG_GEN_BUFFER_SIZE = 10
    MIN_DWELL_COUNT = 10
    MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    SINE_MAX_FREQUENCY = 20000000.
    SQUARE_MAX_FREQUENCY = 20000000.
    TRIANGLE_MAX_FREQUENCY = 20000000.
    SINC_MAX_FREQUENCY = 20000000.
    RAMP_MAX_FREQUENCY = 20000000.
    HALF_SINE_MAX_FREQUENCY = 20000000.
    GAUSSIAN_MAX_FREQUENCY = 20000000.
    MIN_FREQUENCY = 0.03

    # EXT_MAX_VOLTAGE = ?

    def __init__(self, record):
        """
        A wrapper around the PicoScope ps5000 SDK.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        PicoScopeApi.__init__(self, record, ps5000Api_funcptrs)

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, pulse_width_type):
        """
        This function sets up pulse width qualification, which can be used on its own for pulse
        width triggering or combined with window triggering to produce more complex
        triggers. The pulse width qualifier is set by defining one or more conditions structures
        that are then ORed together. Each structure is itself the AND of the states of one or
        more of the inputs. This AND-OR logic allows you to create any possible Boolean
        function of the scope's inputs.

        Populates the :class:`~.picoscope_structs.PS5000PwqConditions` structure.
        """
        conditions = PS5000PwqConditions()
        self.sdk.ps5000SetPulseWidthQualifier(self._handle, byref(conditions), n_conditions, direction, lower,
                                              upper, pulse_width_type)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_conditions(self, n_conditions):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is set up by
        defining one or more :class:`~.picoscope_structs.PS5000TriggerConditions` structures that 
        are then ORed together. Each structure is itself the AND of the states of one or more of 
        the inputs. This AND-OR logic allows you to create any possible Boolean function of the 
        scope's inputs.
        
        If complex triggering is not required, use :meth:`set_simple_trigger`.
        """
        conditions = PS5000TriggerConditions()
        self.sdk.ps5000SetTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_properties(self, n_channel_properties, aux_output_enable, auto_trigger_milliseconds):
        """
        This function is used to enable or disable triggering and set its parameters.

        Populates the :class:`~.picoscope_structs.PS5000TriggerChannelProperties` structure.
        """
        channel_properties = PS5000TriggerChannelProperties()
        self.sdk.ps5000SetTriggerChannelProperties(self._handle, byref(channel_properties), n_channel_properties,
                                                   aux_output_enable, auto_trigger_milliseconds)
        return channel_properties.value  # TODO return structure values

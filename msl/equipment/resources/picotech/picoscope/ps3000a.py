"""
A wrapper around the PicoScope ps3000a SDK.
"""
from ctypes import c_int16, byref

from msl.equipment.resources import register
from .picoscope_api import PicoScopeApi
from .functions import ps3000aApi_funcptrs
from .structs import PS3000ATriggerInfo


@register(manufacturer='Pico\s*Tech', model='3\d{3}[ABD\s]')
class PicoScope3000A(PicoScopeApi):

    MAX_OVERSAMPLE = 256
    PS3207A_MAX_ETS_CYCLES = 500
    PS3207A_MAX_INTERLEAVE = 40
    PS3206A_MAX_ETS_CYCLES = 500
    PS3206A_MAX_INTERLEAVE = 40
    PS3206MSO_MAX_INTERLEAVE = 80
    PS3205A_MAX_ETS_CYCLES = 250
    PS3205A_MAX_INTERLEAVE = 20
    PS3205MSO_MAX_INTERLEAVE = 40
    PS3204A_MAX_ETS_CYCLES = 125
    PS3204A_MAX_INTERLEAVE = 10
    PS3204MSO_MAX_INTERLEAVE = 20
    EXT_MAX_VALUE = 32767
    EXT_MIN_VALUE = -32767
    MAX_LOGIC_LEVEL = 32767
    MIN_LOGIC_LEVEL = -32767
    MIN_SIG_GEN_FREQ = 0.0
    MAX_SIG_GEN_FREQ = 20000000.0
    PS3207B_MAX_SIG_GEN_BUFFER_SIZE = 32768
    PS3206B_MAX_SIG_GEN_BUFFER_SIZE = 16384
    MAX_SIG_GEN_BUFFER_SIZE = 8192
    MIN_SIG_GEN_BUFFER_SIZE = 1
    MIN_DWELL_COUNT = 3
    MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    MAX_ANALOGUE_OFFSET_50MV_200MV = 0.250
    MIN_ANALOGUE_OFFSET_50MV_200MV = -0.250
    MAX_ANALOGUE_OFFSET_500MV_2V = 2.500
    MIN_ANALOGUE_OFFSET_500MV_2V = -2.500
    MAX_ANALOGUE_OFFSET_5V_20V = 20.
    MIN_ANALOGUE_OFFSET_5V_20V = -20.
    SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN = 0xFFFFFFFF
    SINE_MAX_FREQUENCY = 1000000.
    SQUARE_MAX_FREQUENCY = 1000000.
    TRIANGLE_MAX_FREQUENCY = 1000000.
    SINC_MAX_FREQUENCY = 1000000.
    RAMP_MAX_FREQUENCY = 1000000.
    HALF_SINE_MAX_FREQUENCY = 1000000.
    GAUSSIAN_MAX_FREQUENCY = 1000000.
    PRBS_MAX_FREQUENCY = 1000000.
    PRBS_MIN_FREQUENCY = 0.03
    MIN_FREQUENCY = 0.03

    # EXT_MAX_VOLTAGE = ?

    def __init__(self, record):
        """A wrapper around the PicoScope ps3000a SDK.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        PicoScopeApi.__init__(self, record, ps3000aApi_funcptrs)

    def get_max_ets_values(self):
        """
        This function returns the maximum number of cycles and maximum interleaving factor
        that can be used for the selected scope device in ETS mode. These values are the
        upper limits for the ``etsCycles`` and ``etsInterleave`` arguments supplied to
        :meth:`~.PicoScopeApi.set_ets`.
        """
        ets_cycles = c_int16()
        ets_interleave = c_int16()
        self.sdk.ps3000aGetMaxEtsValues(self._handle, byref(ets_cycles), byref(ets_interleave))
        return ets_cycles.value, ets_interleave.value

    def get_trigger_info_bulk(self, from_segment_index, to_segment_index):
        """
        This function returns trigger information in rapid block mode.

        Returns
        -------
        The :class:`~.structs.PS3000ATriggerInfo` structure.
        """
        trigger_info = PS3000ATriggerInfo()
        self.sdk.ps3000aGetTriggerInfoBulk(self._handle, byref(trigger_info), from_segment_index, to_segment_index)
        return trigger_info

    def set_pulse_width_digital_port_properties(self, directions):
        """
        This function will set the individual digital channels' pulse-width trigger directions.
        Each trigger direction consists of a channel name and a direction. If the channel is not
        included in the array of :class:`~.structs.PS3000ADigitalChannelDirections`
        the driver assumes the digital channel's pulse-width trigger direction is
        ``PS3000A_DIGITAL_DONT_CARE``.
        """
        return self.sdk.ps3000aSetPulseWidthDigitalPortProperties(self._handle, byref(directions), len(directions))

    def set_pulse_width_qualifier_v2(self, conditions, direction, lower, upper, pulse_width_type):
        """
        This function sets up pulse-width qualification, which can be used on its own for pulse
        width triggering or combined with level triggering or window triggering to produce
        more complex triggers. The pulse-width qualifier is set by defining one or more
        structures that are then ``ORed`` together. Each structure is itself the ``AND`` of the states of
        one or more of the inputs. This ``AND-OR`` logic allows you to create any possible
        Boolean function of the scope's inputs.
        """
        return self.sdk.ps3000aSetPulseWidthQualifierV2(self._handle, byref(conditions), len(conditions),
                                                        direction, lower, upper, pulse_width_type)

    def set_trigger_channel_conditions_v2(self, conditions):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is defined by
        one or more :class:`~.structs.PS3000ATriggerConditionsV2` structures that are then
        ORed together. Each structure is itself the AND of the states of one or more of the inputs.
        This AND-OR logic allows you to create any possible Boolean function of the scope's
        inputs.

        If complex triggering is not required, use :meth:`~.PicoScopeApi.set_simple_trigger`.
        """
        return self.sdk.ps3000aSetTriggerChannelConditionsV2(self._handle, byref(conditions), len(conditions))

    def set_trigger_digital_port_properties(self, directions):
        """
        This function will set the individual digital channels' trigger directions. Each trigger
        direction consists of a channel name and a direction. If the channel is not included in
        the array of :class:`~.structs.PS3000ADigitalChannelDirections` the driver
        assumes the digital channel's trigger direction is ``PS3000A_DIGITAL_DONT_CARE``.
        """
        return self.sdk.ps3000aSetTriggerDigitalPortProperties(self._handle, byref(directions), len(directions))

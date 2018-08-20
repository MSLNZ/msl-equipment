"""
A wrapper around the PicoScope ps2000a SDK.
"""
from ctypes import byref

from msl.equipment.resources import register
from .picoscope_api import PicoScopeApi
from .functions import ps2000aApi_funcptrs


@register(manufacturer='Pico\s*Tech', model='240[5678][AB]|220(5A MSO|5 MSO|6|7|8)')
class PicoScope2000A(PicoScopeApi):

    PS2208_MAX_ETS_CYCLES = 500
    PS2208_MAX_INTERLEAVE = 20
    PS2207_MAX_ETS_CYCLES = 500
    PS2207_MAX_INTERLEAVE = 20
    PS2206_MAX_ETS_CYCLES = 250
    PS2206_MAX_INTERLEAVE = 10
    EXT_MAX_VALUE = 32767
    EXT_MIN_VALUE = -32767
    MAX_LOGIC_LEVEL = 32767
    MIN_LOGIC_LEVEL = -32767
    MIN_SIG_GEN_FREQ = 0.0
    MAX_SIG_GEN_FREQ = 20000000.0
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
        """A wrapper around the PicoScope ps2000a SDK.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(PicoScope2000A, self).__init__(record, ps2000aApi_funcptrs)

    def set_digital_analog_trigger_operand(self, operand):
        """
        This function is define in the header file, but it is not in the manual.
        """
        return self.sdk.ps2000aSetDigitalAnalogTriggerOperand(self._handle, operand)

    def set_trigger_digital_port_properties(self, directions):
        """
        This function will set the individual Digital channels trigger directions. Each trigger
        direction consists of a channel name and a direction. If the channel is not included in
        the array of :class:`~.structs.PS2000ADigitalChannelDirections` the driver
        assumes the digital channel's trigger direction is ``PS2000A_DIGITAL_DONT_CARE``.
        """
        return self.sdk.ps2000aSetTriggerDigitalPortProperties(self._handle, byref(directions), len(directions))

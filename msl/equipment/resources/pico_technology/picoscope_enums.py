from enum import IntEnum


class PicoScopeInfo(IntEnum):
    """
    Constants that can be passed to the 
    :meth:`~.picoscope_api.PicoscopeApi.get_unit_info` method.
    """
    PICO_DRIVER_VERSION            = 0x00000000
    PICO_USB_VERSION               = 0x00000001
    PICO_HARDWARE_VERSION          = 0x00000002
    PICO_VARIANT_INFO              = 0x00000003
    PICO_BATCH_AND_SERIAL          = 0x00000004
    PICO_CAL_DATE                  = 0x00000005
    PICO_KERNEL_VERSION            = 0x00000006
    PICO_DIGITAL_HARDWARE_VERSION  = 0x00000007
    PICO_ANALOGUE_HARDWARE_VERSION = 0x00000008
    PICO_FIRMWARE_VERSION_1        = 0x00000009
    PICO_FIRMWARE_VERSION_2        = 0x0000000A


# ************************* typedef enum for ps2000 *************************


class PS2000Channel(IntEnum):
    CHANNEL_A    = 0
    CHANNEL_B    = 1
    CHANNEL_C    = 2
    CHANNEL_D    = 3
    EXTERNAL     = 4
    MAX_CHANNELS = EXTERNAL
    NONE         = 5


class PS2000Range(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    MAX_RANGES = 12


class PS2000TimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS2000Error(IntEnum):
    OK               = 0
    MAX_UNITS_OPENED = 1
    MEM_FAIL         = 2
    NOT_FOUND        = 3
    FW_FAIL          = 4
    NOT_RESPONDING   = 5
    CONFIG_FAIL      = 6
    OS_NOT_SUPPORTED = 7
    PICOPP_TOO_OLD   = 8


class PS2000Info(IntEnum):
    DRIVER_VERSION        = 0
    USB_VERSION           = 1
    HARDWARE_VERSION      = 2
    VARIANT_INFO          = 3
    BATCH_AND_SERIAL      = 4
    CAL_DATE              = 5
    ERROR_CODE            = 6
    KERNEL_DRIVER_VERSION = 7


class PS2000TriggerDirection(IntEnum):
    RISING   = 0
    FALLING  = 1
    MAX_DIRS = 2


class PS2000OpenProgress(IntEnum):
    OPEN_PROGRESS_FAIL     = -1
    OPEN_PROGRESS_PENDING  = 0
    OPEN_PROGRESS_COMPLETE = 1


class PS2000EtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS2000ButtonState(IntEnum):
    NO_PRESS    = 0
    SHORT_PRESS = 1
    LONG_PRESS  = 2


class PS2000SweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS2000WaveType(IntEnum):
    SINE       = 0
    SQUARE     = 1
    TRIANGLE   = 2
    RAMPUP     = 3
    RAMPDOWN   = 4
    DC_VOLTAGE = 5
    GAUSSIAN   = 6
    SINC       = 7
    HALF_SINE  = 8


class PS2000ThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    ADV_RISING        = 2
    ADV_FALLING       = 3
    RISING_OR_FALLING = 4
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = ADV_RISING
    EXIT              = ADV_FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    ADV_NONE          = ADV_RISING


class PS2000ThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS2000TriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS2000PulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


# ************************* typedef enum for ps2000aApi *************************


class PS2000AChannelBufferIndex(IntEnum):
    CHANNEL_A_MAX       = 0
    CHANNEL_A_MIN       = 1
    CHANNEL_B_MAX       = 2
    CHANNEL_B_MIN       = 3
    CHANNEL_C_MAX       = 4
    CHANNEL_C_MIN       = 5
    CHANNEL_D_MAX       = 6
    CHANNEL_D_MIN       = 7
    MAX_CHANNEL_BUFFERS = 8


class PS2000AChannel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    EXTERNAL            = 4
    MAX_CHANNELS        = EXTERNAL
    TRIGGER_AUX         = 5
    MAX_TRIGGER_SOURCES = 6


class PS2000ATriggerOperand(IntEnum):
    OPERAND_NONE = 0
    OPERAND_OR   = 1
    OPERAND_AND  = 2
    OPERAND_THEN = 3


class PS2000DigitalPort(IntEnum):
    DIGITAL_PORT0     = 0x80
    DIGITAL_PORT1     = 0x81
    DIGITAL_PORT2     = 0x82
    DIGITAL_PORT3     = 0x83
    MAX_DIGITAL_PORTS = (DIGITAL_PORT3 - DIGITAL_PORT0) + 1


class PS2000ADigitalChannel(IntEnum):
    DIGITAL_CHANNEL_0    = 0
    DIGITAL_CHANNEL_1    = 1
    DIGITAL_CHANNEL_2    = 2
    DIGITAL_CHANNEL_3    = 3
    DIGITAL_CHANNEL_4    = 4
    DIGITAL_CHANNEL_5    = 5
    DIGITAL_CHANNEL_6    = 6
    DIGITAL_CHANNEL_7    = 7
    DIGITAL_CHANNEL_8    = 8
    DIGITAL_CHANNEL_9    = 9
    DIGITAL_CHANNEL_10   = 10
    DIGITAL_CHANNEL_11   = 11
    DIGITAL_CHANNEL_12   = 12
    DIGITAL_CHANNEL_13   = 13
    DIGITAL_CHANNEL_14   = 14
    DIGITAL_CHANNEL_15   = 15
    DIGITAL_CHANNEL_16   = 16
    DIGITAL_CHANNEL_17   = 17
    DIGITAL_CHANNEL_18   = 18
    DIGITAL_CHANNEL_19   = 19
    DIGITAL_CHANNEL_20   = 20
    DIGITAL_CHANNEL_21   = 21
    DIGITAL_CHANNEL_22   = 22
    DIGITAL_CHANNEL_23   = 23
    DIGITAL_CHANNEL_24   = 24
    DIGITAL_CHANNEL_25   = 25
    DIGITAL_CHANNEL_26   = 26
    DIGITAL_CHANNEL_27   = 27
    DIGITAL_CHANNEL_28   = 28
    DIGITAL_CHANNEL_29   = 29
    DIGITAL_CHANNEL_30   = 30
    DIGITAL_CHANNEL_31   = 31
    MAX_DIGITAL_CHANNELS = 32


class PS2000ARange(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    MAX_RANGES = 12


class PS2000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS2000AChannelInfo(IntEnum):
    CI_RANGES = 0


class PS2000AEtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS2000ATimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS2000ASweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS2000AWaveType(IntEnum):
    SINE           = 0
    SQUARE         = 1
    TRIANGLE       = 2
    RAMP_UP        = 3
    RAMP_DOWN      = 4
    SINC           = 5
    GAUSSIAN       = 6
    HALF_SINE      = 7
    DC_VOLTAGE     = 8
    MAX_WAVE_TYPES = 9


class PS2000AExtraOperations(IntEnum):
    ES_OFF     = 0
    WHITENOISE = 1
    PRBS       = 2


class PS2000ASigGenTrigType(IntEnum):
    SIGGEN_RISING    = 0
    SIGGEN_FALLING   = 1
    SIGGEN_GATE_HIGH = 2
    SIGGEN_GATE_LOW  = 3


class PS2000ASigGenTrigSource(IntEnum):
    SIGGEN_NONE       = 0
    SIGGEN_SCOPE_TRIG = 1
    SIGGEN_AUX_IN     = 2
    SIGGEN_EXT_IN     = 3
    SIGGEN_SOFT_TRIG  = 4


class PS2000AIndexMode(IntEnum):
    SINGLE          = 0
    DUAL            = 1
    QUAD            = 2
    MAX_INDEX_MODES = 3


class PS2000A_ThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS2000AThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    ABOVE_LOWER       = 5
    BELOW_LOWER       = 6
    RISING_LOWER      = 7
    FALLING_LOWER     = 8
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    POSITIVE_RUNT     = 9
    NEGATIVE_RUNT     = 10
    NONE              = RISING


class PS2000ADigitalDirection(IntEnum):
    DIGITAL_DONT_CARE                   = 0
    DIGITAL_DIRECTION_LOW               = 1
    DIGITAL_DIRECTION_HIGH              = 2
    DIGITAL_DIRECTION_RISING            = 3
    DIGITAL_DIRECTION_FALLING           = 4
    DIGITAL_DIRECTION_RISING_OR_FALLING = 5
    DIGITAL_MAX_DIRECTION               = 6


class PS2000ATriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS2000ARatioMode(IntEnum):
    RATIO_MODE_NONE      = 0
    RATIO_MODE_AGGREGATE = 1
    RATIO_MODE_DECIMATE  = 2
    RATIO_MODE_AVERAGE   = 4


class PS2000APulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


class PS2000AHoldOffType(IntEnum):
    TIME             = 0
    MAX_HOLDOFF_TYPE = 1


# ************************* typedef enum for ps3000 *************************


class PS3000Channel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    EXTERNAL            = 4
    MAX_CHANNELS        = EXTERNAL
    NONE                = 5
    MAX_TRIGGER_SOURCES = 6


class PS3000Range(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    x100V      = 12
    x200V      = 13
    x400V      = 14
    MAX_RANGES = 15


class PS3000WaveTypes(IntEnum):
    SQUARE         = 0
    TRIANGLE       = 1
    SINE           = 2
    MAX_WAVE_TYPES = 3


class PS3000TimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS3000Error(IntEnum):
    OK               = 0
    MAX_UNITS_OPENED = 1
    MEM_FAIL         = 2
    NOT_FOUND        = 3
    FW_FAIL          = 4
    NOT_RESPONDING   = 5
    CONFIG_FAIL      = 6
    OS_NOT_SUPPORTED = 7
    PICOPP_TOO_OLD   = 8


class PS3000Info(IntEnum):
    DRIVER_VERSION        = 0
    USB_VERSION           = 1
    HARDWARE_VERSION      = 2
    VARIANT_INFO          = 3
    BATCH_AND_SERIAL      = 4
    CAL_DATE              = 5
    ERROR_CODE            = 6
    KERNEL_DRIVER_VERSION = 7


class PS3000TriggerDirection(IntEnum):
    RISING   = 0
    FALLING  = 1
    MAX_DIRS = 2


class PS3000OpenProgress(IntEnum):
    OPEN_PROGRESS_FAIL     = -1
    OPEN_PROGRESS_PENDING  = 0
    OPEN_PROGRESS_COMPLETE = 1


class PS3000EtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS3000ThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    NONE              = RISING


class PS3000ThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS3000TriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS3000PulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


# ************************* typedef enum for ps3000aApi *************************


class PS3000ABandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20MHZ = 1


class PS3000AChannelBufferIndex(IntEnum):
    CHANNEL_A_MAX       = 0
    CHANNEL_A_MIN       = 1
    CHANNEL_B_MAX       = 2
    CHANNEL_B_MIN       = 3
    CHANNEL_C_MAX       = 4
    CHANNEL_C_MIN       = 5
    CHANNEL_D_MAX       = 6
    CHANNEL_D_MIN       = 7
    MAX_CHANNEL_BUFFERS = 8


class PS3000AChannel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    EXTERNAL            = 4
    MAX_CHANNELS        = EXTERNAL
    TRIGGER_AUX         = 5
    MAX_TRIGGER_SOURCES = 6


class PS3000ADigitalPort(IntEnum):
    DIGITAL_PORT0     = 0x80
    DIGITAL_PORT1     = 0x81
    DIGITAL_PORT2     = 0x82
    DIGITAL_PORT3     = 0x83
    MAX_DIGITAL_PORTS = (DIGITAL_PORT3 - DIGITAL_PORT0) + 1


class PS3000ADigitalChannel(IntEnum):
    DIGITAL_CHANNEL_0    = 0
    DIGITAL_CHANNEL_1    = 1
    DIGITAL_CHANNEL_2    = 2
    DIGITAL_CHANNEL_3    = 3
    DIGITAL_CHANNEL_4    = 4
    DIGITAL_CHANNEL_5    = 5
    DIGITAL_CHANNEL_6    = 6
    DIGITAL_CHANNEL_7    = 7
    DIGITAL_CHANNEL_8    = 8
    DIGITAL_CHANNEL_9    = 9
    DIGITAL_CHANNEL_10   = 10
    DIGITAL_CHANNEL_11   = 11
    DIGITAL_CHANNEL_12   = 12
    DIGITAL_CHANNEL_13   = 13
    DIGITAL_CHANNEL_14   = 14
    DIGITAL_CHANNEL_15   = 15
    DIGITAL_CHANNEL_16   = 16
    DIGITAL_CHANNEL_17   = 17
    DIGITAL_CHANNEL_18   = 18
    DIGITAL_CHANNEL_19   = 19
    DIGITAL_CHANNEL_20   = 20
    DIGITAL_CHANNEL_21   = 21
    DIGITAL_CHANNEL_22   = 22
    DIGITAL_CHANNEL_23   = 23
    DIGITAL_CHANNEL_24   = 24
    DIGITAL_CHANNEL_25   = 25
    DIGITAL_CHANNEL_26   = 26
    DIGITAL_CHANNEL_27   = 27
    DIGITAL_CHANNEL_28   = 28
    DIGITAL_CHANNEL_29   = 29
    DIGITAL_CHANNEL_30   = 30
    DIGITAL_CHANNEL_31   = 31
    MAX_DIGITAL_CHANNELS = 32


class PS3000ARange(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    MAX_RANGES = 12


class PS3000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS3000AChannelInfo(IntEnum):
    CI_RANGES = 0


class PS3000AEtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS3000ATimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS3000ASweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS3000AWaveType(IntEnum):
    SINE           = 0
    SQUARE         = 1
    TRIANGLE       = 2
    RAMP_UP        = 3
    RAMP_DOWN      = 4
    SINC           = 5
    GAUSSIAN       = 6
    HALF_SINE      = 7
    DC_VOLTAGE     = 8
    MAX_WAVE_TYPES = 9


class PS3000AExtraOperations(IntEnum):
    ES_OFF     = 0
    WHITENOISE = 1
    PRBS       = 2


class PS3000ASigGenTrigType(IntEnum):
    SIGGEN_RISING    = 0
    SIGGEN_FALLING   = 1
    SIGGEN_GATE_HIGH = 2
    SIGGEN_GATE_LOW  = 3


class PS3000ASigGenTrigSource(IntEnum):
    SIGGEN_NONE       = 0
    SIGGEN_SCOPE_TRIG = 1
    SIGGEN_AUX_IN     = 2
    SIGGEN_EXT_IN     = 3
    SIGGEN_SOFT_TRIG  = 4


class PS3000AIndexMode(IntEnum):
    SINGLE          = 0
    DUAL            = 1
    QUAD            = 2
    MAX_INDEX_MODES = 3


class PS3000A_ThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS3000AThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    ABOVE_LOWER       = 5
    BELOW_LOWER       = 6
    RISING_LOWER      = 7
    FALLING_LOWER     = 8
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    POSITIVE_RUNT     = 9
    NEGATIVE_RUNT     = 10
    NONE              = RISING


class PS3000ADigitalDirection(IntEnum):
    DIGITAL_DONT_CARE                   = 0
    DIGITAL_DIRECTION_LOW               = 1
    DIGITAL_DIRECTION_HIGH              = 2
    DIGITAL_DIRECTION_RISING            = 3
    DIGITAL_DIRECTION_FALLING           = 4
    DIGITAL_DIRECTION_RISING_OR_FALLING = 5
    DIGITAL_MAX_DIRECTION               = 6


class PS3000ATriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS3000ARatioMode(IntEnum):
    RATIO_MODE_NONE      = 0
    RATIO_MODE_AGGREGATE = 1
    RATIO_MODE_DECIMATE  = 2
    RATIO_MODE_AVERAGE   = 4


class PS3000APulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


class PS3000AHoldOffType(IntEnum):
    TIME             = 0
    EVENT            = 1
    MAX_HOLDOFF_TYPE = 2


# ************************* typedef enum for ps4000Api *************************


class PS4000ChannelBufferIndex(IntEnum):
    CHANNEL_A_MAX       = 0
    CHANNEL_A_MIN       = 1
    CHANNEL_B_MAX       = 2
    CHANNEL_B_MIN       = 3
    CHANNEL_C_MAX       = 4
    CHANNEL_C_MIN       = 5
    CHANNEL_D_MAX       = 6
    CHANNEL_D_MIN       = 7
    MAX_CHANNEL_BUFFERS = 8


class PS4000Channel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    EXTERNAL            = 4
    MAX_CHANNELS        = EXTERNAL
    TRIGGER_AUX         = 5
    MAX_TRIGGER_SOURCES = 6


class PS4000Range(IntEnum):
    x10MV                 = 0
    x20MV                 = 1
    x50MV                 = 2
    x100MV                = 3
    x200MV                = 4
    x500MV                = 5
    x1V                   = 6
    x2V                   = 7
    x5V                   = 8
    x10V                  = 9
    x20V                  = 10
    x50V                  = 11
    x100V                 = 12
    MAX_RANGES            = 13
    RESISTANCE_100R       = MAX_RANGES
    RESISTANCE_1K         = 14
    RESISTANCE_10K        = 15
    RESISTANCE_100K       = 16
    RESISTANCE_1M         = 17
    MAX_RESISTANCES       = 18
    ACCELEROMETER_10MV    = MAX_RESISTANCES
    ACCELEROMETER_20MV    = 19
    ACCELEROMETER_50MV    = 20
    ACCELEROMETER_100MV   = 21
    ACCELEROMETER_200MV   = 22
    ACCELEROMETER_500MV   = 23
    ACCELEROMETER_1V      = 24
    ACCELEROMETER_2V      = 25
    ACCELEROMETER_5V      = 26
    ACCELEROMETER_10V     = 27
    ACCELEROMETER_20V     = 28
    ACCELEROMETER_50V     = 29
    ACCELEROMETER_100V    = 30
    MAX_ACCELEROMETER     = 31
    TEMPERATURE_UPTO_40   = MAX_ACCELEROMETER
    TEMPERATURE_UPTO_70   = 32
    TEMPERATURE_UPTO_100  = 33
    TEMPERATURE_UPTO_130  = 34
    MAX_TEMPERATURES      = 35
    RESISTANCE_5K         = MAX_TEMPERATURES
    RESISTANCE_25K        = 36
    RESISTANCE_50K        = 37
    MAX_EXTRA_RESISTANCES = 38


class PS4000Probe(IntEnum):
    P_NONE                     = 0
    P_CURRENT_CLAMP_10A        = 1
    P_CURRENT_CLAMP_1000A      = 2
    P_TEMPERATURE_SENSOR       = 3
    P_CURRENT_MEASURING_DEVICE = 4
    P_PRESSURE_SENSOR_50BAR    = 5
    P_PRESSURE_SENSOR_5BAR     = 6
    P_OPTICAL_SWITCH           = 7
    P_UNKNOWN                  = 8
    P_MAX_PROBES               = P_UNKNOWN


class PS4000ChannelInfo(IntEnum):
    CI_RANGES        = 0
    CI_RESISTANCES   = 1
    CI_ACCELEROMETER = 2
    CI_PROBES        = 3
    CI_TEMPERATURES  = 4


class PS4000EtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS4000TimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS4000SweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS4000OperationTypes(IntEnum):
    OP_NONE    = 0
    WHITENOISE = 1
    PRBS       = 2


class PS4000WaveType(IntEnum):
    SINE           = 0
    SQUARE         = 1
    TRIANGLE       = 2
    RAMP_UP        = 3
    RAMP_DOWN      = 4
    SINC           = 5
    GAUSSIAN       = 6
    HALF_SINE      = 7
    DC_VOLTAGE     = 8
    WHITE_NOISE    = 9
    MAX_WAVE_TYPES = 10


class PS4000SigGenTrigType(IntEnum):
    SIGGEN_RISING    = 0
    SIGGEN_FALLING   = 1
    SIGGEN_GATE_HIGH = 2
    SIGGEN_GATE_LOW  = 3


class PS4000SigGenTrigSource(IntEnum):
    SIGGEN_NONE       = 0
    SIGGEN_SCOPE_TRIG = 1
    SIGGEN_AUX_IN     = 2
    SIGGEN_EXT_IN     = 3
    SIGGEN_SOFT_TRIG  = 4


class PS4000IndexMode(IntEnum):
    SINGLE          = 0
    DUAL            = 1
    QUAD            = 2
    MAX_INDEX_MODES = 3


class PS4000ThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS4000ThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    ABOVE_LOWER       = 5
    BELOW_LOWER       = 6
    RISING_LOWER      = 7
    FALLING_LOWER     = 8
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    POSITIVE_RUNT     = 9
    NEGATIVE_RUNT     = 10
    NONE              = RISING


class PS4000TriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS4000RatioMode(IntEnum):
    RATIO_MODE_NONE      = 0
    RATIO_MODE_AGGREGATE = 1
    RATIO_MODE_AVERAGE   = 2


class PS4000PulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


class PS4000Ps4000HoldOffType(IntEnum):
    TIME             = 0
    MAX_HOLDOFF_TYPE = 1


class PS4000FrequencyCounterRange(IntEnum):
    FC_2K  = 0
    FC_20K = 1
    FC_20  = 2
    FC_200 = 3
    FC_MAX = 4


# ************************* typedef enum for ps4000aApi *************************


class PS4000AExtraOperations(IntEnum):
    ES_OFF     = 0
    WHITENOISE = 1
    PRBS       = 2


class PS4000ABandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20KHZ = 1


class PS4000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS4000AChannel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    MAX_4_CHANNELS      = 4
    CHANNEL_E           = MAX_4_CHANNELS
    CHANNEL_F           = 5
    CHANNEL_G           = 6
    CHANNEL_H           = 7
    EXTERNAL            = 8
    MAX_CHANNELS        = EXTERNAL
    TRIGGER_AUX         = 9
    MAX_TRIGGER_SOURCES = 10
    PULSE_WIDTH_SOURCE  = 0x10000000


class PS4000AChannelBufferIndex(IntEnum):
    CHANNEL_A_MAX       = 0
    CHANNEL_A_MIN       = 1
    CHANNEL_B_MAX       = 2
    CHANNEL_B_MIN       = 3
    CHANNEL_C_MAX       = 4
    CHANNEL_C_MIN       = 5
    CHANNEL_D_MAX       = 6
    CHANNEL_D_MIN       = 7
    CHANNEL_E_MAX       = 8
    CHANNEL_E_MIN       = 9
    CHANNEL_F_MAX       = 10
    CHANNEL_F_MIN       = 11
    CHANNEL_G_MAX       = 12
    CHANNEL_G_MIN       = 13
    CHANNEL_H_MAX       = 14
    CHANNEL_H_MIN       = 15
    MAX_CHANNEL_BUFFERS = 16


class PS4000ARange(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    x100V      = 12
    x200V      = 13
    MAX_RANGES = 14


class PS4000AResistanceRange(IntEnum):
    RESISTANCE_315K       = 0x00000200
    RESISTANCE_1100K      = 0x00000201
    RESISTANCE_10M        = 0x00000202
    MAX_RESISTANCE_RANGES = (RESISTANCE_10M + 1) - RESISTANCE_315K
    RESISTANCE_ADCV       = 0x10000000


class PS4000AEtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS4000ATimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS4000ASweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS4000AWaveType(IntEnum):
    SINE           = 0
    SQUARE         = 1
    TRIANGLE       = 2
    RAMP_UP        = 3
    RAMP_DOWN      = 4
    SINC           = 5
    GAUSSIAN       = 6
    HALF_SINE      = 7
    DC_VOLTAGE     = 8
    WHITE_NOISE    = 9
    MAX_WAVE_TYPES = 10


class PS4000AChannelLed(IntEnum):
    CHANNEL_LED_OFF   = 0
    CHANNEL_LED_RED   = 1
    CHANNEL_LED_GREEN = 2


class PS4000AMetaType(IntEnum):
    MT_UNIT_INFO                 = 0
    MT_DEVICE_CAPABILITY         = 1
    MT_DEVICE_SETTINGS           = 2
    MT_SIGNAL_GENERATOR_SETTINGS = 3


class PS4000AMetaOperation(IntEnum):
    MO_READ  = 0
    MO_WRITE = 1


class PS4000AMetaFormat(IntEnum):
    MF_COMMA_SEPERATED = 0
    MF_XML             = 1


class PS4000ASigGenTrigType(IntEnum):
    SIGGEN_RISING    = 0
    SIGGEN_FALLING   = 1
    SIGGEN_GATE_HIGH = 2
    SIGGEN_GATE_LOW  = 3


class PS4000ASigGenTrigSource(IntEnum):
    SIGGEN_NONE       = 0
    SIGGEN_SCOPE_TRIG = 1
    SIGGEN_AUX_IN     = 2
    SIGGEN_EXT_IN     = 3
    SIGGEN_SOFT_TRIG  = 4


class PS4000AIndexMode(IntEnum):
    SINGLE          = 0
    DUAL            = 1
    QUAD            = 2
    MAX_INDEX_MODES = 3


class PS4000AThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS4000AThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    ABOVE_LOWER       = 5
    BELOW_LOWER       = 6
    RISING_LOWER      = 7
    FALLING_LOWER     = 8
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    POSITIVE_RUNT     = 9
    NEGATIVE_RUNT     = 10
    NONE              = RISING


class PS4000ATriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS4000ASensorState(IntEnum):
    CONNECT_STATE_FLOATING = 0
    SENSOR_STATE_CONNECTED = 1


class PS4000AFrequencyCounterRange(IntEnum):
    FC_2K  = 0
    FC_20K = 1
    FC_20  = 2
    FC_200 = 3
    FC_MAX = 4


class PS4000AConditionsInfo(IntEnum):
    CLEAR = 0x00000001
    ADD   = 0x00000002


class PS4000ARatioMode(IntEnum):
    RATIO_MODE_NONE         = 0
    RATIO_MODE_AGGREGATE    = 1
    RATIO_MODE_DECIMATE     = 2
    RATIO_MODE_AVERAGE      = 4
    RATIO_MODE_DISTRIBUTION = 8


class PS4000APulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


class PS4000AChannelInfo(IntEnum):
    CI_RANGES      = 0
    CI_RESISTANCES = 1
# This enum definition was found in PicoStatus.h
# It is used by the ps4000aGetString function


class PicoStringValue(IntEnum):
    PICO_SV_MEMORY                                                = 0
    PICO_SV_MEMORY_NO_OF_SEGMENTS                                 = 1
    PICO_SV_MEMORY_MAX_SAMPLES                                    = 2
    PICO_SV_NO_OF_CHANNELS                                        = 3
    PICO_SV_ARRAY_OF_CHANNELS                                     = 4
    PICO_SV_CHANNEL                                               = 5
    PICO_SV_CHANNEL_NAME                                          = 6
    PICO_SV_CHANNEL_RANGE                                         = 7
    PICO_SV_CHANNEL_COUPLING                                      = 8
    PICO_SV_CHANNEL_ENABLED                                       = 9
    PICO_SV_CHANNEL_ANALOGUE_OFFSET                               = 10
    PICO_SV_CHANNEL_BANDWIDTH                                     = 11
    PICO_SV_TRIGGER                                               = 12
    PICO_SV_TRIGGER_AUXIO_OUTPUT_ENABLED                          = 13
    PICO_SV_TRIGGER_AUTO_TRIGGER_MILLISECONDS                     = 14
    PICO_SV_TRIGGER_PROPERTIES                                    = 15
    PICO_SV_NO_OF_TRIGGER_PROPERTIES                              = 16
    PICO_SV_TRIGGER_PROPERTIES_CHANNEL                            = 17
    PICO_SV_TRIGGER_PROPERTIES_THRESHOLD_UPPER                    = 18
    PICO_SV_TRIGGER_PROPERTIES_THRESHOLD_UPPER_HYSTERESIS         = 19
    PICO_SV_TRIGGER_PROPERTIES_THRESHOLD_LOWER                    = 20
    PICO_SV_TRIGGER_PROPERTIES_THRESHOLD_LOWER_HYSTERESIS         = 21
    PICO_SV_TRIGGER_PROPERTIES_THRESHOLD_MODE                     = 22
    PICO_SV_TRIGGER_ARRAY_OF_BLOCK_CONDITIONS                     = 23
    PICO_SV_TRIGGER_NO_OF_BLOCK_CONDITIONS                        = 24
    PICO_SV_TRIGGER_CONDITIONS                                    = 25
    PICO_SV_TRIGGER_NO_OF_CONDITIONS                              = 26
    PICO_SV_TRIGGER_CONDITION_SOURCE                              = 27
    PICO_SV_TRIGGER_CONDITION_STATE                               = 28
    PICO_SV_TRIGGER_DIRECTION                                     = 29
    PICO_SV_TRIGGER_NO_OF_DIRECTIONS                              = 30
    PICO_SV_TRIGGER_DIRECTION_CHANNEL                             = 31
    PICO_SV_TRIGGER_DIRECTION_DIRECTION                           = 32
    PICO_SV_TRIGGER_DELAY                                         = 33
    PICO_SV_TRIGGER_DELAY_MS                                      = 34
    PICO_SV_FREQUENCY_COUNTER                                     = 35
    PICO_SV_FREQUENCY_COUNTER_ENABLED                             = 36
    PICO_SV_FREQUENCY_COUNTER_CHANNEL                             = 37
    PICO_SV_FREQUENCY_COUNTER_RANGE                               = 38
    PICO_SV_FREQUENCY_COUNTER_TRESHOLDMAJOR                       = 39
    PICO_SV_FREQUENCY_COUNTER_TRESHOLDMINOR                       = 40
    PICO_SV_PULSE_WIDTH_PROPERTIES                                = 41
    PICO_SV_PULSE_WIDTH_PROPERTIES_DIRECTION                      = 42
    PICO_SV_PULSE_WIDTH_PROPERTIES_LOWER                          = 43
    PICO_SV_PULSE_WIDTH_PROPERTIES_UPPER                          = 44
    PICO_SV_PULSE_WIDTH_PROPERTIES_TYPE                           = 45
    PICO_SV_PULSE_WIDTH_ARRAY_OF_BLOCK_CONDITIONS                 = 46
    PICO_SV_PULSE_WIDTH_NO_OF_BLOCK_CONDITIONS                    = 47
    PICO_SV_PULSE_WIDTH_CONDITIONS                                = 48
    PICO_SV_PULSE_WIDTH_NO_OF_CONDITIONS                          = 49
    PICO_SV_PULSE_WIDTH_CONDITIONS_SOURCE                         = 50
    PICO_SV_PULSE_WIDTH_CONDITIONS_STATE                          = 51
    PICO_SV_SAMPLE_PROPERTIES                                     = 52
    PICO_SV_SAMPLE_PROPERTIES_PRE_TRIGGER_SAMPLES                 = 53
    PICO_SV_SAMPLE_PROPERTIES_POST_TRIGGER_SAMPLES                = 54
    PICO_SV_SAMPLE_PROPERTIES_TIMEBASE                            = 55
    PICO_SV_SAMPLE_PROPERTIES_NO_OF_CAPTURES                      = 56
    PICO_SV_SAMPLE_PROPERTIES_RESOLUTION                          = 57
    PICO_SV_SAMPLE_PROPERTIES_OVERLAPPED                          = 58
    PICO_SV_SAMPLE_PROPERTIES_OVERLAPPED_DOWN_SAMPLE_RATIO        = 59
    PICO_SV_SAMPLE_PROPERTIES_OVERLAPPED_DOWN_SAMPLE_RATIO_MODE   = 60
    PICO_SV_SAMPLE_PROPERTIES_OVERLAPPED_REQUERSTED_NO_OF_SAMPLES = 61
    PICO_SV_SAMPLE_PROPERTIES_OVERLAPPED_SEGMENT_INDEX_FROM       = 62
    PICO_SV_SAMPLE_PROPERTIES_OVERLAPPED_SEGMENT_INDEX_TO         = 63
    PICO_SV_SIGNAL_GENERATOR                                      = 64
    PICO_SV_SIGNAL_GENERATOR_BUILT_IN                             = 65
    PICO_SV_SIGNAL_GENERATOR_BUILT_IN_WAVE_TYPE                   = 66
    PICO_SV_SIGNAL_GENERATOR_BUILT_IN_START_FREQUENCY             = 67
    PICO_SV_SIGNAL_GENERATOR_BUILT_IN_STOP_FREQUENCY              = 68
    PICO_SV_SIGNAL_GENERATOR_BUILT_IN_INCREMENT                   = 69
    PICO_SV_SIGNAL_GENERATOR_BUILT_IN_DWELL_TIME                  = 70
    PICO_SV_SIGNAL_GENERATOR_AWG                                  = 71
    PICO_SV_SIGNAL_GENERATOR_AWG_START_DELTA_PHASE                = 72
    PICO_SV_SIGNAL_GENERATOR_AWG_STOP_DELTA_PHASE                 = 73
    PICO_SV_SIGNAL_GENERATOR_AWG_DELTA_PHASE_INCREMENT            = 74
    PICO_SV_SIGNAL_GENERATOR_AWG_DWELL_COUNT                      = 75
    PICO_SV_SIGNAL_GENERATOR_AWG_INDEX_MODE                       = 76
    PICO_SV_SIGNAL_GENERATOR_AWG_WAVEFORM_SIZE                    = 77
    PICO_SV_SIGNAL_GENERATOR_ARRAY_OF_AWG_WAVEFORM_VALUES         = 78
    PICO_SV_SIGNAL_GENERATOR_OFFSET_VOLTAGE                       = 79
    PICO_SV_SIGNAL_GENERATOR_PK_TO_PK                             = 80
    PICO_SV_SIGNAL_GENERATOR_OPERATION                            = 81
    PICO_SV_SIGNAL_GENERATOR_SHOTS                                = 82
    PICO_SV_SIGNAL_GENERATOR_SWEEPS                               = 83
    PICO_SV_SIGNAL_GENERATOR_SWEEP_TYPE                           = 84
    PICO_SV_SIGNAL_GENERATOR_TRIGGER_TYPE                         = 85
    PICO_SV_SIGNAL_GENERATOR_TRIGGER_SOURCE                       = 86
    PICO_SV_SIGNAL_GENERATOR_EXT_IN_THRESHOLD                     = 87
    PICO_SV_ETS                                                   = 88
    PICO_SV_ETS_STATE                                             = 89
    PICO_SV_ETS_CYCLE                                             = 90
    PICO_SV_ETS_INTERLEAVE                                        = 91
    PICO_SV_ETS_SAMPLE_TIME_PICOSECONDS                           = 92


# ************************* typedef enum for ps5000Api *************************


class PS5000Channel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    EXTERNAL            = 4
    MAX_CHANNELS        = EXTERNAL
    TRIGGER_AUX         = 5
    MAX_TRIGGER_SOURCES = 6


class PS5000ChannelBufferIndex(IntEnum):
    CHANNEL_A_MAX       = 0
    CHANNEL_A_MIN       = 1
    CHANNEL_B_MAX       = 2
    CHANNEL_B_MIN       = 3
    CHANNEL_C_MAX       = 4
    CHANNEL_C_MIN       = 5
    CHANNEL_D_MAX       = 6
    CHANNEL_D_MIN       = 7
    MAX_CHANNEL_BUFFERS = 8


class PS5000Range(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    MAX_RANGES = 12


class PS5000EtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS5000TimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS5000SweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS5000WaveType(IntEnum):
    SINE           = 0
    SQUARE         = 1
    TRIANGLE       = 2
    RAMP_UP        = 3
    RAMP_DOWN      = 4
    SINC           = 5
    GAUSSIAN       = 6
    HALF_SINE      = 7
    DC_VOLTAGE     = 8
    WHITE_NOISE    = 9
    MAX_WAVE_TYPES = 10


class PS5000SigGenTrigType(IntEnum):
    SIGGEN_RISING    = 0
    SIGGEN_FALLING   = 1
    SIGGEN_GATE_HIGH = 2
    SIGGEN_GATE_LOW  = 3


class PS5000SigGenTrigSource(IntEnum):
    SIGGEN_NONE       = 0
    SIGGEN_SCOPE_TRIG = 1
    SIGGEN_AUX_IN     = 2
    SIGGEN_EXT_IN     = 3
    SIGGEN_SOFT_TRIG  = 4


class PS5000IndexMode(IntEnum):
    SINGLE          = 0
    DUAL            = 1
    QUAD            = 2
    MAX_INDEX_MODES = 3


class PS5000ThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS5000ThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    NONE              = RISING


class PS5000TriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS5000RatioMode(IntEnum):
    RATIO_MODE_NONE         = 0
    RATIO_MODE_AGGREGATE    = 1
    RATIO_MODE_DECIMATE     = 2
    RATIO_MODE_AVERAGE      = 4
    RATIO_MODE_DISTRIBUTION = 8


class PS5000PulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


class PS5000ChannelInfo(IntEnum):
    CI_RANGES = 0


# ************************* typedef enum for ps5000aApi *************************


class PS5000ADeviceResolution(IntEnum):
    DR_8BIT  = 0
    DR_12BIT = 1
    DR_14BIT = 2
    DR_15BIT = 3
    DR_16BIT = 4


class PS5000AExtraOperations(IntEnum):
    ES_OFF     = 0
    WHITENOISE = 1
    PRBS       = 2


class PS5000ABandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20MHZ = 1


class PS5000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS5000AChannel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    EXTERNAL            = 4
    MAX_CHANNELS        = EXTERNAL
    TRIGGER_AUX         = 5
    MAX_TRIGGER_SOURCES = 6


class PS5000AChannelBufferIndex(IntEnum):
    CHANNEL_A_MAX       = 0
    CHANNEL_A_MIN       = 1
    CHANNEL_B_MAX       = 2
    CHANNEL_B_MIN       = 3
    CHANNEL_C_MAX       = 4
    CHANNEL_C_MIN       = 5
    CHANNEL_D_MAX       = 6
    CHANNEL_D_MIN       = 7
    MAX_CHANNEL_BUFFERS = 8


class PS5000ARange(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    MAX_RANGES = 12


class PS5000AEtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS5000ATimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS5000ASweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS5000AWaveType(IntEnum):
    SINE           = 0
    SQUARE         = 1
    TRIANGLE       = 2
    RAMP_UP        = 3
    RAMP_DOWN      = 4
    SINC           = 5
    GAUSSIAN       = 6
    HALF_SINE      = 7
    DC_VOLTAGE     = 8
    WHITE_NOISE    = 9
    MAX_WAVE_TYPES = 10


class PS5000ASigGenTrigType(IntEnum):
    SIGGEN_RISING    = 0
    SIGGEN_FALLING   = 1
    SIGGEN_GATE_HIGH = 2
    SIGGEN_GATE_LOW  = 3


class PS5000ASigGenTrigSource(IntEnum):
    SIGGEN_NONE       = 0
    SIGGEN_SCOPE_TRIG = 1
    SIGGEN_AUX_IN     = 2
    SIGGEN_EXT_IN     = 3
    SIGGEN_SOFT_TRIG  = 4


class PS5000AIndexMode(IntEnum):
    SINGLE          = 0
    DUAL            = 1
    QUAD            = 2
    MAX_INDEX_MODES = 3


class PS5000AThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS5000AThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    ABOVE_LOWER       = 5
    BELOW_LOWER       = 6
    RISING_LOWER      = 7
    FALLING_LOWER     = 8
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    POSITIVE_RUNT     = 9
    NEGATIVE_RUNT     = 10
    NONE              = RISING


class PS5000ATriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS5000ATriggerWithinPreTrigger(IntEnum):
    DISABLE = 0
    ARM     = 1


class PS5000ARatioMode(IntEnum):
    RATIO_MODE_NONE         = 0
    RATIO_MODE_AGGREGATE    = 1
    RATIO_MODE_DECIMATE     = 2
    RATIO_MODE_AVERAGE      = 4
    RATIO_MODE_DISTRIBUTION = 8


class PS5000APulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


class PS5000AChannelInfo(IntEnum):
    CI_RANGES = 0


# ************************* typedef enum for ps6000Api *************************


class PS6000ExternalFrequency(IntEnum):
    FREQUENCY_OFF   = 0
    FREQUENCY_5MHZ  = 1
    FREQUENCY_10MHZ = 2
    FREQUENCY_20MHZ = 3
    FREQUENCY_25MHZ = 4
    MAX_FREQUENCIES = 5


class PS6000BandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20MHZ = 1
    BW_25MHZ = 2


class PS6000Channel(IntEnum):
    CHANNEL_A           = 0
    CHANNEL_B           = 1
    CHANNEL_C           = 2
    CHANNEL_D           = 3
    EXTERNAL            = 4
    MAX_CHANNELS        = EXTERNAL
    TRIGGER_AUX         = 5
    MAX_TRIGGER_SOURCES = 6


class PS6000ChannelBufferIndex(IntEnum):
    CHANNEL_A_MAX       = 0
    CHANNEL_A_MIN       = 1
    CHANNEL_B_MAX       = 2
    CHANNEL_B_MIN       = 3
    CHANNEL_C_MAX       = 4
    CHANNEL_C_MIN       = 5
    CHANNEL_D_MAX       = 6
    CHANNEL_D_MIN       = 7
    MAX_CHANNEL_BUFFERS = 8


class PS6000Range(IntEnum):
    x10MV      = 0
    x20MV      = 1
    x50MV      = 2
    x100MV     = 3
    x200MV     = 4
    x500MV     = 5
    x1V        = 6
    x2V        = 7
    x5V        = 8
    x10V       = 9
    x20V       = 10
    x50V       = 11
    MAX_RANGES = 12


class PS6000Coupling(IntEnum):
    AC     = 0
    DC_1M  = 1
    DC_50R = 2


class PS6000EtsMode(IntEnum):
    ETS_OFF       = 0
    ETS_FAST      = 1
    ETS_SLOW      = 2
    ETS_MODES_MAX = 3


class PS6000TimeUnits(IntEnum):
    FS             = 0
    PS             = 1
    NS             = 2
    US             = 3
    MS             = 4
    S              = 5
    MAX_TIME_UNITS = 6


class PS6000SweepType(IntEnum):
    UP              = 0
    DOWN            = 1
    UPDOWN          = 2
    DOWNUP          = 3
    MAX_SWEEP_TYPES = 4


class PS6000WaveType(IntEnum):
    SINE           = 0
    SQUARE         = 1
    TRIANGLE       = 2
    RAMP_UP        = 3
    RAMP_DOWN      = 4
    SINC           = 5
    GAUSSIAN       = 6
    HALF_SINE      = 7
    DC_VOLTAGE     = 8
    MAX_WAVE_TYPES = 9


class PS6000ExtraOperations(IntEnum):
    ES_OFF     = 0
    WHITENOISE = 1
    PRBS       = 2


class PS6000SigGenTrigType(IntEnum):
    SIGGEN_RISING    = 0
    SIGGEN_FALLING   = 1
    SIGGEN_GATE_HIGH = 2
    SIGGEN_GATE_LOW  = 3


class PS6000SigGenTrigSource(IntEnum):
    SIGGEN_NONE        = 0
    SIGGEN_SCOPE_TRIG  = 1
    SIGGEN_AUX_IN      = 2
    SIGGEN_EXT_IN      = 3
    SIGGEN_SOFT_TRIG   = 4
    SIGGEN_TRIGGER_RAW = 5


class PS6000IndexMode(IntEnum):
    SINGLE          = 0
    DUAL            = 1
    QUAD            = 2
    MAX_INDEX_MODES = 3


class PS6000ThresholdMode(IntEnum):
    LEVEL  = 0
    WINDOW = 1


class PS6000ThresholdDirection(IntEnum):
    ABOVE             = 0
    BELOW             = 1
    RISING            = 2
    FALLING           = 3
    RISING_OR_FALLING = 4
    ABOVE_LOWER       = 5
    BELOW_LOWER       = 6
    RISING_LOWER      = 7
    FALLING_LOWER     = 8
    INSIDE            = ABOVE
    OUTSIDE           = BELOW
    ENTER             = RISING
    EXIT              = FALLING
    ENTER_OR_EXIT     = RISING_OR_FALLING
    POSITIVE_RUNT     = 9
    NEGATIVE_RUNT     = 10
    NONE              = RISING


class PS6000TriggerState(IntEnum):
    CONDITION_DONT_CARE = 0
    CONDITION_TRUE      = 1
    CONDITION_FALSE     = 2
    CONDITION_MAX       = 3


class PS6000RatioMode(IntEnum):
    RATIO_MODE_NONE         = 0
    RATIO_MODE_AGGREGATE    = 1
    RATIO_MODE_AVERAGE      = 2
    RATIO_MODE_DECIMATE     = 4
    RATIO_MODE_DISTRIBUTION = 8


class PS6000PulseWidthType(IntEnum):
    PW_TYPE_NONE         = 0
    PW_TYPE_LESS_THAN    = 1
    PW_TYPE_GREATER_THAN = 2
    PW_TYPE_IN_RANGE     = 3
    PW_TYPE_OUT_OF_RANGE = 4


ENUM_DATA_TYPE_NAMES = [
    'INDEX_MODE',
    'PICO_STRING_VALUE',
    'PS2000A_CHANNEL',
    'PS2000A_CHANNEL_BUFFER_INDEX',
    'PS2000A_CHANNEL_INFO',
    'PS2000A_COUPLING',
    'PS2000A_DIGITAL_CHANNEL',
    'PS2000A_DIGITAL_DIRECTION',
    'PS2000A_DIGITAL_PORT',
    'PS2000A_ETS_MODE',
    'PS2000A_EXTRA_OPERATIONS',
    'PS2000A_HOLDOFF_TYPE',
    'PS2000A_INDEX_MODE',
    'PS2000A_PULSE_WIDTH_TYPE',
    'PS2000A_RANGE',
    'PS2000A_RATIO_MODE',
    'PS2000A_SIGGEN_TRIG_SOURCE',
    'PS2000A_SIGGEN_TRIG_TYPE',
    'PS2000A_SWEEP_TYPE',
    'PS2000A_THRESHOLD_DIRECTION',
    'PS2000A_THRESHOLD_MODE',
    'PS2000A_TIME_UNITS',
    'PS2000A_TRIGGER_OPERAND',
    'PS2000A_TRIGGER_STATE',
    'PS2000A_WAVE_TYPE',
    'PS2000_BUTTON_STATE',
    'PS2000_CHANNEL',
    'PS2000_ERROR',
    'PS2000_ETS_MODE',
    'PS2000_INFO',
    'PS2000_OPEN_PROGRESS',
    'PS2000_PULSE_WIDTH_TYPE',
    'PS2000_RANGE',
    'PS2000_SWEEP_TYPE',
    'PS2000_TDIR',
    'PS2000_THRESHOLD_DIRECTION',
    'PS2000_THRESHOLD_MODE',
    'PS2000_TIME_UNITS',
    'PS2000_TRIGGER_STATE',
    'PS2000_WAVE_TYPE',
    'PS3000A_BANDWIDTH_LIMITER',
    'PS3000A_CHANNEL',
    'PS3000A_CHANNEL_BUFFER_INDEX',
    'PS3000A_CHANNEL_INFO',
    'PS3000A_COUPLING',
    'PS3000A_DIGITAL_CHANNEL',
    'PS3000A_DIGITAL_DIRECTION',
    'PS3000A_DIGITAL_PORT',
    'PS3000A_ETS_MODE',
    'PS3000A_EXTRA_OPERATIONS',
    'PS3000A_HOLDOFF_TYPE',
    'PS3000A_INDEX_MODE',
    'PS3000A_PULSE_WIDTH_TYPE',
    'PS3000A_RANGE',
    'PS3000A_RATIO_MODE',
    'PS3000A_SIGGEN_TRIG_SOURCE',
    'PS3000A_SIGGEN_TRIG_TYPE',
    'PS3000A_SWEEP_TYPE',
    'PS3000A_THRESHOLD_DIRECTION',
    'PS3000A_THRESHOLD_MODE',
    'PS3000A_TIME_UNITS',
    'PS3000A_TRIGGER_STATE',
    'PS3000A_WAVE_TYPE',
    'PS3000_CHANNEL',
    'PS3000_ERROR',
    'PS3000_ETS_MODE',
    'PS3000_INFO',
    'PS3000_OPEN_PROGRESS',
    'PS3000_RANGE',
    'PS3000_TDIR',
    'PS3000_TIME_UNITS',
    'PS3000_WAVE_TYPES',
    'PS4000A_BANDWIDTH_LIMITER',
    'PS4000A_CHANNEL',
    'PS4000A_CHANNEL_BUFFER_INDEX',
    'PS4000A_CHANNEL_INFO',
    'PS4000A_CHANNEL_LED',
    'PS4000A_CONDITIONS_INFO',
    'PS4000A_COUPLING',
    'PS4000A_ETS_MODE',
    'PS4000A_EXTRA_OPERATIONS',
    'PS4000A_FREQUENCY_COUNTER_RANGE',
    'PS4000A_INDEX_MODE',
    'PS4000A_META_FORMAT',
    'PS4000A_META_OPERATION',
    'PS4000A_META_TYPE',
    'PS4000A_PULSE_WIDTH_TYPE',
    'PS4000A_RANGE',
    'PS4000A_RATIO_MODE',
    'PS4000A_RESISTANCE_RANGE',
    'PS4000A_SENSOR_STATE',
    'PS4000A_SIGGEN_TRIG_SOURCE',
    'PS4000A_SIGGEN_TRIG_TYPE',
    'PS4000A_SWEEP_TYPE',
    'PS4000A_THRESHOLD_DIRECTION',
    'PS4000A_THRESHOLD_MODE',
    'PS4000A_TIME_UNITS',
    'PS4000A_TRIGGER_STATE',
    'PS4000A_WAVE_TYPE',
    'PS4000_CHANNEL',
    'PS4000_CHANNEL_BUFFER_INDEX',
    'PS4000_CHANNEL_INFO',
    'PS4000_ETS_MODE',
    'PS4000_FREQUENCY_COUNTER_RANGE',
    'PS4000_HOLDOFF_TYPE',
    'PS4000_OPERATION_TYPES',
    'PS4000_PROBE',
    'PS4000_RANGE',
    'PS4000_TIME_UNITS',
    'PS5000A_BANDWIDTH_LIMITER',
    'PS5000A_CHANNEL',
    'PS5000A_CHANNEL_BUFFER_INDEX',
    'PS5000A_CHANNEL_INFO',
    'PS5000A_COUPLING',
    'PS5000A_DEVICE_RESOLUTION',
    'PS5000A_ETS_MODE',
    'PS5000A_EXTRA_OPERATIONS',
    'PS5000A_INDEX_MODE',
    'PS5000A_PULSE_WIDTH_TYPE',
    'PS5000A_RANGE',
    'PS5000A_RATIO_MODE',
    'PS5000A_SIGGEN_TRIG_SOURCE',
    'PS5000A_SIGGEN_TRIG_TYPE',
    'PS5000A_SWEEP_TYPE',
    'PS5000A_THRESHOLD_DIRECTION',
    'PS5000A_THRESHOLD_MODE',
    'PS5000A_TIME_UNITS',
    'PS5000A_TRIGGER_STATE',
    'PS5000A_TRIGGER_WITHIN_PRE_TRIGGER',
    'PS5000A_WAVE_TYPE',
    'PS5000_CHANNEL',
    'PS5000_CHANNEL_BUFFER_INDEX',
    'PS5000_CHANNEL_INFO',
    'PS5000_ETS_MODE',
    'PS5000_RANGE',
    'PS5000_TIME_UNITS',
    'PS6000_BANDWIDTH_LIMITER',
    'PS6000_CHANNEL',
    'PS6000_CHANNEL_BUFFER_INDEX',
    'PS6000_COUPLING',
    'PS6000_ETS_MODE',
    'PS6000_EXTERNAL_FREQUENCY',
    'PS6000_EXTRA_OPERATIONS',
    'PS6000_INDEX_MODE',
    'PS6000_PULSE_WIDTH_TYPE',
    'PS6000_RANGE',
    'PS6000_RATIO_MODE',
    'PS6000_SIGGEN_TRIG_SOURCE',
    'PS6000_SIGGEN_TRIG_TYPE',
    'PS6000_SWEEP_TYPE',
    'PS6000_THRESHOLD_DIRECTION',
    'PS6000_THRESHOLD_MODE',
    'PS6000_TIME_UNITS',
    'PS6000_TRIGGER_STATE',
    'PS6000_WAVE_TYPE',
    'PULSE_WIDTH_TYPE',
    'RATIO_MODE',
    'SIGGEN_TRIG_SOURCE',
    'SIGGEN_TRIG_TYPE',
    'SWEEP_TYPE',
    'THRESHOLD_DIRECTION',
    'THRESHOLD_MODE',
    'TRIGGER_STATE',
    'WAVE_TYPE',
]

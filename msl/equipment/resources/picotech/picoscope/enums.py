from enum import IntEnum


class PicoScopeInfoApi(IntEnum):
    """
    Constants that can be passed to the 
    :meth:`~.picoscope_api.PicoscopeApi.get_unit_info` method.
    """
    DRIVER_VERSION            = 0x00000000
    USB_VERSION               = 0x00000001
    HARDWARE_VERSION          = 0x00000002
    VARIANT_INFO              = 0x00000003
    BATCH_AND_SERIAL          = 0x00000004
    CAL_DATE                  = 0x00000005
    KERNEL_VERSION            = 0x00000006
    DIGITAL_HARDWARE_VERSION  = 0x00000007
    ANALOGUE_HARDWARE_VERSION = 0x00000008
    FIRMWARE_VERSION_1        = 0x00000009
    FIRMWARE_VERSION_2        = 0x0000000A


# ************************* typedef enum for ps2000 *************************


class PS2000Channel(IntEnum):
    A            = 0
    B            = 1
    C            = 2
    D            = 3
    EXT          = 4
    MAX_CHANNELS = EXT
    NONE         = 5


class PS2000Range(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_MAX   = 12


class PS2000TimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


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
    MAX      = 2


class PS2000OpenProgress(IntEnum):
    FAIL     = -1
    PENDING  = 0
    COMPLETE = 1


class PS2000EtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS2000ButtonState(IntEnum):
    NO_PRESS    = 0
    SHORT_PRESS = 1
    LONG_PRESS  = 2


class PS2000SweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


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
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS2000PulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


# ************************* typedef enum for ps2000aApi *************************


class PS2000AChannelBufferIndex(IntEnum):
    A_MAX = 0
    A_MIN = 1
    B_MAX = 2
    B_MIN = 3
    C_MAX = 4
    C_MIN = 5
    D_MAX = 6
    D_MIN = 7
    MAX   = 8


class PS2000AChannel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    EXT                 = 4
    MAX_CHANNELS        = EXT
    AUX                 = 5
    MAX_TRIGGER_SOURCES = 6


class PS2000ATriggerOperand(IntEnum):
    NONE = 0
    OR   = 1
    AND  = 2
    THEN = 3


class PS2000DigitalPort(IntEnum):
    PORT0 = 0x80
    PORT1 = 0x81
    PORT2 = 0x82
    PORT3 = 0x83
    MAX   = (PORT3 - PORT0) + 1


class PS2000ADigitalChannel(IntEnum):
    CHANNEL_0   = 0
    CHANNEL_1   = 1
    CHANNEL_2   = 2
    CHANNEL_3   = 3
    CHANNEL_4   = 4
    CHANNEL_5   = 5
    CHANNEL_6   = 6
    CHANNEL_7   = 7
    CHANNEL_8   = 8
    CHANNEL_9   = 9
    CHANNEL_10  = 10
    CHANNEL_11  = 11
    CHANNEL_12  = 12
    CHANNEL_13  = 13
    CHANNEL_14  = 14
    CHANNEL_15  = 15
    CHANNEL_16  = 16
    CHANNEL_17  = 17
    CHANNEL_18  = 18
    CHANNEL_19  = 19
    CHANNEL_20  = 20
    CHANNEL_21  = 21
    CHANNEL_22  = 22
    CHANNEL_23  = 23
    CHANNEL_24  = 24
    CHANNEL_25  = 25
    CHANNEL_26  = 26
    CHANNEL_27  = 27
    CHANNEL_28  = 28
    CHANNEL_29  = 29
    CHANNEL_30  = 30
    CHANNEL_31  = 31
    CHANNEL_MAX = 32


class PS2000ARange(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_MAX   = 12


class PS2000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS2000AChannelInfo(IntEnum):
    RANGES = 0


class PS2000AEtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS2000ATimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


class PS2000ASweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


class PS2000AWaveType(IntEnum):
    SINE       = 0
    SQUARE     = 1
    TRIANGLE   = 2
    RAMP_UP    = 3
    RAMP_DOWN  = 4
    SINC       = 5
    GAUSSIAN   = 6
    HALF_SINE  = 7
    DC_VOLTAGE = 8
    MAX        = 9


class PS2000AExtraOperations(IntEnum):
    OFF        = 0
    WHITENOISE = 1
    PRBS       = 2


class PS2000ASigGenTrigType(IntEnum):
    RISING    = 0
    FALLING   = 1
    GATE_HIGH = 2
    GATE_LOW  = 3


class PS2000ASigGenTrigSource(IntEnum):
    NONE       = 0
    SCOPE_TRIG = 1
    AUX_IN     = 2
    EXT_IN     = 3
    SOFT_TRIG  = 4


class PS2000AIndexMode(IntEnum):
    SINGLE = 0
    DUAL   = 1
    QUAD   = 2
    MAX    = 3


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
    DONT_CARE         = 0
    LOW               = 1
    HIGH              = 2
    RISING            = 3
    FALLING           = 4
    RISING_OR_FALLING = 5
    MAX               = 6


class PS2000ATriggerState(IntEnum):
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS2000ARatioMode(IntEnum):
    NONE      = 0
    AGGREGATE = 1
    DECIMATE  = 2
    AVERAGE   = 4


class PS2000APulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


class PS2000AHoldOffType(IntEnum):
    TIME = 0
    MAX  = 1


# ************************* typedef enum for ps3000 *************************


class PS3000Channel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    EXT                 = 4
    MAX_CHANNELS        = EXT
    NONE                = 5
    MAX_TRIGGER_SOURCES = 6


class PS3000Range(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_100V  = 12
    R_200V  = 13
    R_400V  = 14
    R_MAX   = 15


class PS3000WaveTypes(IntEnum):
    SQUARE   = 0
    TRIANGLE = 1
    SINE     = 2
    MAX      = 3


class PS3000TimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


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
    MAX      = 2


class PS3000OpenProgress(IntEnum):
    FAIL     = -1
    PENDING  = 0
    COMPLETE = 1


class PS3000EtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


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
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS3000PulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


# ************************* typedef enum for ps3000aApi *************************


class PS3000ABandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20MHZ = 1


class PS3000AChannelBufferIndex(IntEnum):
    A_MAX = 0
    A_MIN = 1
    B_MAX = 2
    B_MIN = 3
    C_MAX = 4
    C_MIN = 5
    D_MAX = 6
    D_MIN = 7
    MAX   = 8


class PS3000AChannel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    EXT                 = 4
    MAX_CHANNELS        = EXT
    AUX                 = 5
    MAX_TRIGGER_SOURCES = 6


class PS3000ADigitalPort(IntEnum):
    PORT0 = 0x80
    PORT1 = 0x81
    PORT2 = 0x82
    PORT3 = 0x83
    MAX   = (PORT3 - PORT0) + 1


class PS3000ADigitalChannel(IntEnum):
    CHANNEL_0   = 0
    CHANNEL_1   = 1
    CHANNEL_2   = 2
    CHANNEL_3   = 3
    CHANNEL_4   = 4
    CHANNEL_5   = 5
    CHANNEL_6   = 6
    CHANNEL_7   = 7
    CHANNEL_8   = 8
    CHANNEL_9   = 9
    CHANNEL_10  = 10
    CHANNEL_11  = 11
    CHANNEL_12  = 12
    CHANNEL_13  = 13
    CHANNEL_14  = 14
    CHANNEL_15  = 15
    CHANNEL_16  = 16
    CHANNEL_17  = 17
    CHANNEL_18  = 18
    CHANNEL_19  = 19
    CHANNEL_20  = 20
    CHANNEL_21  = 21
    CHANNEL_22  = 22
    CHANNEL_23  = 23
    CHANNEL_24  = 24
    CHANNEL_25  = 25
    CHANNEL_26  = 26
    CHANNEL_27  = 27
    CHANNEL_28  = 28
    CHANNEL_29  = 29
    CHANNEL_30  = 30
    CHANNEL_31  = 31
    CHANNEL_MAX = 32


class PS3000ARange(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_MAX   = 12


class PS3000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS3000AChannelInfo(IntEnum):
    RANGES = 0


class PS3000AEtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS3000ATimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


class PS3000ASweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


class PS3000AWaveType(IntEnum):
    SINE       = 0
    SQUARE     = 1
    TRIANGLE   = 2
    RAMP_UP    = 3
    RAMP_DOWN  = 4
    SINC       = 5
    GAUSSIAN   = 6
    HALF_SINE  = 7
    DC_VOLTAGE = 8
    MAX        = 9


class PS3000AExtraOperations(IntEnum):
    OFF        = 0
    WHITENOISE = 1
    PRBS       = 2


class PS3000ASigGenTrigType(IntEnum):
    RISING    = 0
    FALLING   = 1
    GATE_HIGH = 2
    GATE_LOW  = 3


class PS3000ASigGenTrigSource(IntEnum):
    NONE       = 0
    SCOPE_TRIG = 1
    AUX_IN     = 2
    EXT_IN     = 3
    SOFT_TRIG  = 4


class PS3000AIndexMode(IntEnum):
    SINGLE = 0
    DUAL   = 1
    QUAD   = 2
    MAX    = 3


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
    DONT_CARE         = 0
    LOW               = 1
    HIGH              = 2
    RISING            = 3
    FALLING           = 4
    RISING_OR_FALLING = 5
    MAX               = 6


class PS3000ATriggerState(IntEnum):
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS3000ARatioMode(IntEnum):
    NONE      = 0
    AGGREGATE = 1
    DECIMATE  = 2
    AVERAGE   = 4


class PS3000APulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


class PS3000AHoldOffType(IntEnum):
    TIME  = 0
    EVENT = 1
    MAX   = 2


# ************************* typedef enum for ps4000Api *************************


class PS4000ChannelBufferIndex(IntEnum):
    A_MAX = 0
    A_MIN = 1
    B_MAX = 2
    B_MIN = 3
    C_MAX = 4
    C_MIN = 5
    D_MAX = 6
    D_MIN = 7
    MAX   = 8


class PS4000Channel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    EXT                 = 4
    MAX_CHANNELS        = EXT
    AUX                 = 5
    MAX_TRIGGER_SOURCES = 6


class PS4000Range(IntEnum):
    R_10MV                = 0
    R_20MV                = 1
    R_50MV                = 2
    R_100MV               = 3
    R_200MV               = 4
    R_500MV               = 5
    R_1V                  = 6
    R_2V                  = 7
    R_5V                  = 8
    R_10V                 = 9
    R_20V                 = 10
    R_50V                 = 11
    R_100V                = 12
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
    NONE                     = 0
    CURRENT_CLAMP_10A        = 1
    CURRENT_CLAMP_1000A      = 2
    TEMPERATURE_SENSOR       = 3
    CURRENT_MEASURING_DEVICE = 4
    PRESSURE_SENSOR_50BAR    = 5
    PRESSURE_SENSOR_5BAR     = 6
    OPTICAL_SWITCH           = 7
    UNKNOWN                  = 8
    MAX_PROBES               = UNKNOWN


class PS4000ChannelInfo(IntEnum):
    RANGES        = 0
    RESISTANCES   = 1
    ACCELEROMETER = 2
    PROBES        = 3
    TEMPERATURES  = 4


class PS4000EtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS4000TimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


class PS4000SweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


class PS4000OperationTypes(IntEnum):
    NONE    = 0
    WHITENOISE = 1
    PRBS       = 2


class PS4000WaveType(IntEnum):
    SINE        = 0
    SQUARE      = 1
    TRIANGLE    = 2
    RAMP_UP     = 3
    RAMP_DOWN   = 4
    SINC        = 5
    GAUSSIAN    = 6
    HALF_SINE   = 7
    DC_VOLTAGE  = 8
    WHITE_NOISE = 9
    MAX         = 10


class PS4000SigGenTrigType(IntEnum):
    RISING    = 0
    FALLING   = 1
    GATE_HIGH = 2
    GATE_LOW  = 3


class PS4000SigGenTrigSource(IntEnum):
    NONE       = 0
    SCOPE_TRIG = 1
    AUX_IN     = 2
    EXT_IN     = 3
    SOFT_TRIG  = 4


class PS4000IndexMode(IntEnum):
    SINGLE = 0
    DUAL   = 1
    QUAD   = 2
    MAX    = 3


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
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS4000RatioMode(IntEnum):
    NONE      = 0
    AGGREGATE = 1
    AVERAGE   = 2


class PS4000PulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


class PS4000Ps4000HoldOffType(IntEnum):
    TIME = 0
    MAX  = 1


class PS4000FrequencyCounterRange(IntEnum):
    FC_2K  = 0
    FC_20K = 1
    FC_20  = 2
    FC_200 = 3
    FC_MAX = 4


# ************************* typedef enum for ps4000aApi *************************


class PS4000AExtraOperations(IntEnum):
    OFF        = 0
    WHITENOISE = 1
    PRBS       = 2


class PS4000ABandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20KHZ = 1


class PS4000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS4000AChannel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    MAX_4_CHANNELS      = 4
    E                   = MAX_4_CHANNELS
    F                   = 5
    G                   = 6
    H                   = 7
    EXT                 = 8
    MAX_CHANNELS        = EXT
    AUX                 = 9
    MAX_TRIGGER_SOURCES = 10
    PULSE_WIDTH_SOURCE  = 0x10000000


class PS4000AChannelBufferIndex(IntEnum):
    A_MAX = 0
    A_MIN = 1
    B_MAX = 2
    B_MIN = 3
    C_MAX = 4
    C_MIN = 5
    D_MAX = 6
    D_MIN = 7
    E_MAX = 8
    E_MIN = 9
    F_MAX = 10
    F_MIN = 11
    G_MAX = 12
    G_MIN = 13
    H_MAX = 14
    H_MIN = 15
    MAX   = 16


class PS4000ARange(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_100V  = 12
    R_200V  = 13
    R_MAX   = 14


class PS4000AResistanceRange(IntEnum):
    R_315K  = 0x00000200
    R_1100K = 0x00000201
    R_10M   = 0x00000202
    R_MAX   = (R_10M + 1) - R_315K
    R_ADCV  = 0x10000000


class PS4000AEtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS4000ATimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


class PS4000ASweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


class PS4000AWaveType(IntEnum):
    SINE        = 0
    SQUARE      = 1
    TRIANGLE    = 2
    RAMP_UP     = 3
    RAMP_DOWN   = 4
    SINC        = 5
    GAUSSIAN    = 6
    HALF_SINE   = 7
    DC_VOLTAGE  = 8
    WHITE_NOISE = 9
    MAX         = 10


class PS4000AChannelLed(IntEnum):
    OFF   = 0
    RED   = 1
    GREEN = 2


class PS4000AMetaType(IntEnum):
    UNIT_INFO                 = 0
    DEVICE_CAPABILITY         = 1
    DEVICE_SETTINGS           = 2
    SIGNAL_GENERATOR_SETTINGS = 3


class PS4000AMetaOperation(IntEnum):
    READ  = 0
    WRITE = 1


class PS4000AMetaFormat(IntEnum):
    COMMA_SEPERATED = 0
    XML             = 1


class PS4000ASigGenTrigType(IntEnum):
    RISING    = 0
    FALLING   = 1
    GATE_HIGH = 2
    GATE_LOW  = 3


class PS4000ASigGenTrigSource(IntEnum):
    NONE       = 0
    SCOPE_TRIG = 1
    AUX_IN     = 2
    EXT_IN     = 3
    SOFT_TRIG  = 4


class PS4000AIndexMode(IntEnum):
    SINGLE = 0
    DUAL   = 1
    QUAD   = 2
    MAX    = 3


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
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


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
    NONE         = 0
    AGGREGATE    = 1
    DECIMATE     = 2
    AVERAGE      = 4
    DISTRIBUTION = 8


class PS4000APulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


class PS4000AChannelInfo(IntEnum):
    RANGES      = 0
    RESISTANCES = 1

# This enum definition was found in PicoStatus.h
# It is used by the ps4000aGetString function
class PS4000APicoStringValue(IntEnum):
    MEMORY                                                = 0
    MEMORY_NO_OF_SEGMENTS                                 = 1
    MEMORY_MAX_SAMPLES                                    = 2
    NO_OF_CHANNELS                                        = 3
    ARRAY_OF_CHANNELS                                     = 4
    CHANNEL                                               = 5
    CHANNEL_NAME                                          = 6
    CHANNEL_RANGE                                         = 7
    CHANNEL_COUPLING                                      = 8
    CHANNEL_ENABLED                                       = 9
    CHANNEL_ANALOGUE_OFFSET                               = 10
    CHANNEL_BANDWIDTH                                     = 11
    TRIGGER                                               = 12
    TRIGGER_AUXIO_OUTPUT_ENABLED                          = 13
    TRIGGER_AUTO_TRIGGER_MILLISECONDS                     = 14
    TRIGGER_PROPERTIES                                    = 15
    NO_OF_TRIGGER_PROPERTIES                              = 16
    TRIGGER_PROPERTIES_CHANNEL                            = 17
    TRIGGER_PROPERTIES_THRESHOLD_UPPER                    = 18
    TRIGGER_PROPERTIES_THRESHOLD_UPPER_HYSTERESIS         = 19
    TRIGGER_PROPERTIES_THRESHOLD_LOWER                    = 20
    TRIGGER_PROPERTIES_THRESHOLD_LOWER_HYSTERESIS         = 21
    TRIGGER_PROPERTIES_THRESHOLD_MODE                     = 22
    TRIGGER_ARRAY_OF_BLOCK_CONDITIONS                     = 23
    TRIGGER_NO_OF_BLOCK_CONDITIONS                        = 24
    TRIGGER_CONDITIONS                                    = 25
    TRIGGER_NO_OF_CONDITIONS                              = 26
    TRIGGER_CONDITION_SOURCE                              = 27
    TRIGGER_CONDITION_STATE                               = 28
    TRIGGER_DIRECTION                                     = 29
    TRIGGER_NO_OF_DIRECTIONS                              = 30
    TRIGGER_DIRECTION_CHANNEL                             = 31
    TRIGGER_DIRECTION_DIRECTION                           = 32
    TRIGGER_DELAY                                         = 33
    TRIGGER_DELAY_MS                                      = 34
    FREQUENCY_COUNTER                                     = 35
    FREQUENCY_COUNTER_ENABLED                             = 36
    FREQUENCY_COUNTER_CHANNEL                             = 37
    FREQUENCY_COUNTER_RANGE                               = 38
    FREQUENCY_COUNTER_TRESHOLDMAJOR                       = 39
    FREQUENCY_COUNTER_TRESHOLDMINOR                       = 40
    PULSE_WIDTH_PROPERTIES                                = 41
    PULSE_WIDTH_PROPERTIES_DIRECTION                      = 42
    PULSE_WIDTH_PROPERTIES_LOWER                          = 43
    PULSE_WIDTH_PROPERTIES_UPPER                          = 44
    PULSE_WIDTH_PROPERTIES_TYPE                           = 45
    PULSE_WIDTH_ARRAY_OF_BLOCK_CONDITIONS                 = 46
    PULSE_WIDTH_NO_OF_BLOCK_CONDITIONS                    = 47
    PULSE_WIDTH_CONDITIONS                                = 48
    PULSE_WIDTH_NO_OF_CONDITIONS                          = 49
    PULSE_WIDTH_CONDITIONS_SOURCE                         = 50
    PULSE_WIDTH_CONDITIONS_STATE                          = 51
    SAMPLE_PROPERTIES                                     = 52
    SAMPLE_PROPERTIES_PRE_TRIGGER_SAMPLES                 = 53
    SAMPLE_PROPERTIES_POST_TRIGGER_SAMPLES                = 54
    SAMPLE_PROPERTIES_TIMEBASE                            = 55
    SAMPLE_PROPERTIES_NO_OF_CAPTURES                      = 56
    SAMPLE_PROPERTIES_RESOLUTION                          = 57
    SAMPLE_PROPERTIES_OVERLAPPED                          = 58
    SAMPLE_PROPERTIES_OVERLAPPED_DOWN_SAMPLE_RATIO        = 59
    SAMPLE_PROPERTIES_OVERLAPPED_DOWN_SAMPLE_RATIO_MODE   = 60
    SAMPLE_PROPERTIES_OVERLAPPED_REQUERSTED_NO_OF_SAMPLES = 61
    SAMPLE_PROPERTIES_OVERLAPPED_SEGMENT_INDEX_FROM       = 62
    SAMPLE_PROPERTIES_OVERLAPPED_SEGMENT_INDEX_TO         = 63
    SIGNAL_GENERATOR                                      = 64
    SIGNAL_GENERATOR_BUILT_IN                             = 65
    SIGNAL_GENERATOR_BUILT_IN_WAVE_TYPE                   = 66
    SIGNAL_GENERATOR_BUILT_IN_START_FREQUENCY             = 67
    SIGNAL_GENERATOR_BUILT_IN_STOP_FREQUENCY              = 68
    SIGNAL_GENERATOR_BUILT_IN_INCREMENT                   = 69
    SIGNAL_GENERATOR_BUILT_IN_DWELL_TIME                  = 70
    SIGNAL_GENERATOR_AWG                                  = 71
    SIGNAL_GENERATOR_AWG_START_DELTA_PHASE                = 72
    SIGNAL_GENERATOR_AWG_STOP_DELTA_PHASE                 = 73
    SIGNAL_GENERATOR_AWG_DELTA_PHASE_INCREMENT            = 74
    SIGNAL_GENERATOR_AWG_DWELL_COUNT                      = 75
    SIGNAL_GENERATOR_AWG_INDEX_MODE                       = 76
    SIGNAL_GENERATOR_AWG_WAVEFORM_SIZE                    = 77
    SIGNAL_GENERATOR_ARRAY_OF_AWG_WAVEFORM_VALUES         = 78
    SIGNAL_GENERATOR_OFFSET_VOLTAGE                       = 79
    SIGNAL_GENERATOR_PK_TO_PK                             = 80
    SIGNAL_GENERATOR_OPERATION                            = 81
    SIGNAL_GENERATOR_SHOTS                                = 82
    SIGNAL_GENERATOR_SWEEPS                               = 83
    SIGNAL_GENERATOR_SWEEP_TYPE                           = 84
    SIGNAL_GENERATOR_TRIGGER_TYPE                         = 85
    SIGNAL_GENERATOR_TRIGGER_SOURCE                       = 86
    SIGNAL_GENERATOR_EXT_IN_THRESHOLD                     = 87
    ETS                                                   = 88
    ETS_STATE                                             = 89
    ETS_CYCLE                                             = 90
    ETS_INTERLEAVE                                        = 91
    ETS_SAMPLE_TIME_PICOSECONDS                           = 92


# ************************* typedef enum for ps5000Api *************************


class PS5000Channel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    EXT                 = 4
    MAX_CHANNELS        = EXT
    AUX                 = 5
    MAX_TRIGGER_SOURCES = 6


class PS5000ChannelBufferIndex(IntEnum):
    A_MAX = 0
    A_MIN = 1
    B_MAX = 2
    B_MIN = 3
    C_MAX = 4
    C_MIN = 5
    D_MAX = 6
    D_MIN = 7
    MAX   = 8


class PS5000Range(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_MAX   = 12


class PS5000EtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS5000TimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


class PS5000SweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


class PS5000WaveType(IntEnum):
    SINE        = 0
    SQUARE      = 1
    TRIANGLE    = 2
    RAMP_UP     = 3
    RAMP_DOWN   = 4
    SINC        = 5
    GAUSSIAN    = 6
    HALF_SINE   = 7
    DC_VOLTAGE  = 8
    WHITE_NOISE = 9
    MAX         = 10


class PS5000SigGenTrigType(IntEnum):
    RISING    = 0
    FALLING   = 1
    GATE_HIGH = 2
    GATE_LOW  = 3


class PS5000SigGenTrigSource(IntEnum):
    NONE       = 0
    SCOPE_TRIG = 1
    AUX_IN     = 2
    EXT_IN     = 3
    SOFT_TRIG  = 4


class PS5000IndexMode(IntEnum):
    SINGLE = 0
    DUAL   = 1
    QUAD   = 2
    MAX    = 3


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
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS5000RatioMode(IntEnum):
    NONE         = 0
    AGGREGATE    = 1
    DECIMATE     = 2
    AVERAGE      = 4
    DISTRIBUTION = 8


class PS5000PulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


class PS5000ChannelInfo(IntEnum):
    RANGES = 0


# ************************* typedef enum for ps5000aApi *************************


class PS5000ADeviceResolution(IntEnum):
    RES_8BIT  = 0
    RES_12BIT = 1
    RES_14BIT = 2
    RES_15BIT = 3
    RES_16BIT = 4


class PS5000AExtraOperations(IntEnum):
    OFF        = 0
    WHITENOISE = 1
    PRBS       = 2


class PS5000ABandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20MHZ = 1


class PS5000ACoupling(IntEnum):
    AC = 0
    DC = 1


class PS5000AChannel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    EXT                 = 4
    MAX_CHANNELS        = EXT
    AUX                 = 5
    MAX_TRIGGER_SOURCES = 6


class PS5000AChannelBufferIndex(IntEnum):
    A_MAX = 0
    A_MIN = 1
    B_MAX = 2
    B_MIN = 3
    C_MAX = 4
    C_MIN = 5
    D_MAX = 6
    D_MIN = 7
    MAX   = 8


class PS5000ARange(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_MAX   = 12


class PS5000AEtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS5000ATimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


class PS5000ASweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


class PS5000AWaveType(IntEnum):
    SINE        = 0
    SQUARE      = 1
    TRIANGLE    = 2
    RAMP_UP     = 3
    RAMP_DOWN   = 4
    SINC        = 5
    GAUSSIAN    = 6
    HALF_SINE   = 7
    DC_VOLTAGE  = 8
    WHITE_NOISE = 9
    MAX         = 10


class PS5000ASigGenTrigType(IntEnum):
    RISING    = 0
    FALLING   = 1
    GATE_HIGH = 2
    GATE_LOW  = 3


class PS5000ASigGenTrigSource(IntEnum):
    NONE       = 0
    SCOPE_TRIG = 1
    AUX_IN     = 2
    EXT_IN     = 3
    SOFT_TRIG  = 4


class PS5000AIndexMode(IntEnum):
    SINGLE = 0
    DUAL   = 1
    QUAD   = 2
    MAX    = 3


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
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS5000ATriggerWithinPreTrigger(IntEnum):
    DISABLE = 0
    ARM     = 1


class PS5000ARatioMode(IntEnum):
    NONE         = 0
    AGGREGATE    = 1
    DECIMATE     = 2
    AVERAGE      = 4
    DISTRIBUTION = 8


class PS5000APulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


class PS5000AChannelInfo(IntEnum):
    RANGES = 0


# ************************* typedef enum for ps6000Api *************************


class PS6000ExternalFrequency(IntEnum):
    EF_OFF   = 0
    EF_5MHZ  = 1
    EF_10MHZ = 2
    EF_20MHZ = 3
    EF_25MHZ = 4
    EF_MAX   = 5


class PS6000BandwidthLimiter(IntEnum):
    BW_FULL  = 0
    BW_20MHZ = 1
    BW_25MHZ = 2


class PS6000Channel(IntEnum):
    A                   = 0
    B                   = 1
    C                   = 2
    D                   = 3
    EXT                 = 4
    MAX_CHANNELS        = EXT
    AUX                 = 5
    MAX_TRIGGER_SOURCES = 6


class PS6000ChannelBufferIndex(IntEnum):
    A_MAX = 0
    A_MIN = 1
    B_MAX = 2
    B_MIN = 3
    C_MAX = 4
    C_MIN = 5
    D_MAX = 6
    D_MIN = 7
    MAX   = 8


class PS6000Range(IntEnum):
    R_10MV  = 0
    R_20MV  = 1
    R_50MV  = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V    = 6
    R_2V    = 7
    R_5V    = 8
    R_10V   = 9
    R_20V   = 10
    R_50V   = 11
    R_MAX   = 12


class PS6000Coupling(IntEnum):
    AC     = 0
    DC_1M  = 1
    DC_50R = 2


class PS6000EtsMode(IntEnum):
    OFF  = 0
    FAST = 1
    SLOW = 2
    MAX  = 3


class PS6000TimeUnits(IntEnum):
    FS  = 0
    PS  = 1
    NS  = 2
    US  = 3
    MS  = 4
    S   = 5
    MAX = 6


class PS6000SweepType(IntEnum):
    UP     = 0
    DOWN   = 1
    UPDOWN = 2
    DOWNUP = 3
    MAX    = 4


class PS6000WaveType(IntEnum):
    SINE       = 0
    SQUARE     = 1
    TRIANGLE   = 2
    RAMP_UP    = 3
    RAMP_DOWN  = 4
    SINC       = 5
    GAUSSIAN   = 6
    HALF_SINE  = 7
    DC_VOLTAGE = 8
    MAX        = 9


class PS6000ExtraOperations(IntEnum):
    OFF        = 0
    WHITENOISE = 1
    PRBS       = 2


class PS6000SigGenTrigType(IntEnum):
    RISING    = 0
    FALLING   = 1
    GATE_HIGH = 2
    GATE_LOW  = 3


class PS6000SigGenTrigSource(IntEnum):
    NONE        = 0
    SCOPE_TRIG  = 1
    AUX_IN      = 2
    EXT_IN      = 3
    SOFT_TRIG   = 4
    TRIGGER_RAW = 5


class PS6000IndexMode(IntEnum):
    SINGLE = 0
    DUAL   = 1
    QUAD   = 2
    MAX    = 3


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
    DONT_CARE = 0
    TRUE      = 1
    FALSE     = 2
    MAX       = 3


class PS6000RatioMode(IntEnum):
    NONE         = 0
    AGGREGATE    = 1
    AVERAGE      = 2
    DECIMATE     = 4
    DISTRIBUTION = 8


class PS6000PulseWidthType(IntEnum):
    NONE         = 0
    LESS_THAN    = 1
    GREATER_THAN = 2
    IN_RANGE     = 3
    OUT_OF_RANGE = 4


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

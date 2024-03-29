"""
Exceptions and error codes defined in the Pico Technology SDK.
"""
from __future__ import annotations

from ctypes import c_uint32
from enum import IntEnum

PICO_MAC_ADDRESS                                 = 0x0000000B

PICO_INFO                                        = c_uint32

PICO_OK                                          = 0x00000000
PICO_MAX_UNITS_OPENED                            = 0x00000001
PICO_MEMORY_FAIL                                 = 0x00000002
PICO_NOT_FOUND                                   = 0x00000003
PICO_FW_FAIL                                     = 0x00000004
PICO_OPEN_OPERATION_IN_PROGRESS                  = 0x00000005
PICO_OPERATION_FAILED                            = 0x00000006
PICO_NOT_RESPONDING                              = 0x00000007
PICO_CONFIG_FAIL                                 = 0x00000008
PICO_KERNEL_DRIVER_TOO_OLD                       = 0x00000009
PICO_EEPROM_CORRUPT                              = 0x0000000A
PICO_OS_NOT_SUPPORTED                            = 0x0000000B
PICO_INVALID_HANDLE                              = 0x0000000C
PICO_INVALID_PARAMETER                           = 0x0000000D
PICO_INVALID_TIMEBASE                            = 0x0000000E
PICO_INVALID_VOLTAGE_RANGE                       = 0x0000000F
PICO_INVALID_CHANNEL                             = 0x00000010
PICO_INVALID_TRIGGER_CHANNEL                     = 0x00000011
PICO_INVALID_CONDITION_CHANNEL                   = 0x00000012
PICO_NO_SIGNAL_GENERATOR                         = 0x00000013
PICO_STREAMING_FAILED                            = 0x00000014
PICO_BLOCK_MODE_FAILED                           = 0x00000015
PICO_NULL_PARAMETER                              = 0x00000016
PICO_ETS_MODE_SET                                = 0x00000017
PICO_DATA_NOT_AVAILABLE                          = 0x00000018
PICO_STRING_BUFFER_TOO_SMALL                     = 0x00000019
PICO_ETS_NOT_SUPPORTED                           = 0x0000001A
PICO_AUTO_TRIGGER_TIME_TOO_SHORT                 = 0x0000001B
PICO_BUFFER_STALL                                = 0x0000001C
PICO_TOO_MANY_SAMPLES                            = 0x0000001D
PICO_TOO_MANY_SEGMENTS                           = 0x0000001E
PICO_PULSE_WIDTH_QUALIFIER                       = 0x0000001F
PICO_DELAY                                       = 0x00000020
PICO_SOURCE_DETAILS                              = 0x00000021
PICO_CONDITIONS                                  = 0x00000022
PICO_USER_CALLBACK                               = 0x00000023
PICO_DEVICE_SAMPLING                             = 0x00000024
PICO_NO_SAMPLES_AVAILABLE                        = 0x00000025
PICO_SEGMENT_OUT_OF_RANGE                        = 0x00000026
PICO_BUSY                                        = 0x00000027
PICO_STARTINDEX_INVALID                          = 0x00000028
PICO_INVALID_INFO                                = 0x00000029
PICO_INFO_UNAVAILABLE                            = 0x0000002A
PICO_INVALID_SAMPLE_INTERVAL                     = 0x0000002B
PICO_TRIGGER_ERROR                               = 0x0000002C
PICO_MEMORY                                      = 0x0000002D
PICO_SIG_GEN_PARAM                               = 0x0000002E
PICO_SHOTS_SWEEPS_WARNING                        = 0x0000002F
PICO_SIGGEN_TRIGGER_SOURCE                       = 0x00000030
PICO_AUX_OUTPUT_CONFLICT                         = 0x00000031
PICO_AUX_OUTPUT_ETS_CONFLICT                     = 0x00000032
PICO_WARNING_EXT_THRESHOLD_CONFLICT              = 0x00000033
PICO_WARNING_AUX_OUTPUT_CONFLICT                 = 0x00000034
PICO_SIGGEN_OUTPUT_OVER_VOLTAGE                  = 0x00000035
PICO_DELAY_NULL                                  = 0x00000036
PICO_INVALID_BUFFER                              = 0x00000037
PICO_SIGGEN_OFFSET_VOLTAGE                       = 0x00000038
PICO_SIGGEN_PK_TO_PK                             = 0x00000039
PICO_CANCELLED                                   = 0x0000003A
PICO_SEGMENT_NOT_USED                            = 0x0000003B
PICO_INVALID_CALL                                = 0x0000003C
PICO_GET_VALUES_INTERRUPTED                      = 0x0000003D
PICO_NOT_USED                                    = 0x0000003F
PICO_INVALID_SAMPLERATIO                         = 0x00000040
PICO_INVALID_STATE                               = 0x00000041
PICO_NOT_ENOUGH_SEGMENTS                         = 0x00000042
PICO_DRIVER_FUNCTION                             = 0x00000043
PICO_RESERVED                                    = 0x00000044
PICO_INVALID_COUPLING                            = 0x00000045
PICO_BUFFERS_NOT_SET                             = 0x00000046
PICO_RATIO_MODE_NOT_SUPPORTED                    = 0x00000047
PICO_RAPID_NOT_SUPPORT_AGGREGATION               = 0x00000048
PICO_INVALID_TRIGGER_PROPERTY                    = 0x00000049
PICO_INTERFACE_NOT_CONNECTED                     = 0x0000004A
PICO_RESISTANCE_AND_PROBE_NOT_ALLOWED            = 0x0000004B
PICO_POWER_FAILED                                = 0x0000004C
PICO_SIGGEN_WAVEFORM_SETUP_FAILED                = 0x0000004D
PICO_FPGA_FAIL                                   = 0x0000004E
PICO_POWER_MANAGER                               = 0x0000004F
PICO_INVALID_ANALOGUE_OFFSET                     = 0x00000050
PICO_PLL_LOCK_FAILED                             = 0x00000051
PICO_ANALOG_BOARD                                = 0x00000052
PICO_CONFIG_FAIL_AWG                             = 0x00000053
PICO_INITIALISE_FPGA                             = 0x00000054
PICO_EXTERNAL_FREQUENCY_INVALID                  = 0x00000056
PICO_CLOCK_CHANGE_ERROR                          = 0x00000057
PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH            = 0x00000058
PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH                = 0x00000059
PICO_UNABLE_TO_OPEN_SCALING_FILE                 = 0x0000005A
PICO_MEMORY_CLOCK_FREQUENCY                      = 0x0000005B
PICO_I2C_NOT_RESPONDING                          = 0x0000005C
PICO_NO_CAPTURES_AVAILABLE                       = 0x0000005D
PICO_NOT_USED_IN_THIS_CAPTURE_MODE               = 0x0000005E
PICO_GET_DATA_ACTIVE                             = 0x00000103
PICO_IP_NETWORKED                                = 0x00000104
PICO_INVALID_IP_ADDRESS                          = 0x00000105
PICO_IPSOCKET_FAILED                             = 0x00000106
PICO_IPSOCKET_TIMEDOUT                           = 0x00000107
PICO_SETTINGS_FAILED                             = 0x00000108
PICO_NETWORK_FAILED                              = 0x00000109
PICO_WS2_32_DLL_NOT_LOADED                       = 0x0000010A
PICO_INVALID_IP_PORT                             = 0x0000010B
PICO_COUPLING_NOT_SUPPORTED                      = 0x0000010C
PICO_BANDWIDTH_NOT_SUPPORTED                     = 0x0000010D
PICO_INVALID_BANDWIDTH                           = 0x0000010E
PICO_AWG_NOT_SUPPORTED                           = 0x0000010F
PICO_ETS_NOT_RUNNING                             = 0x00000110
PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED            = 0x00000111
PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED              = 0x00000112
PICO_INVALID_DIGITAL_PORT                        = 0x00000113
PICO_INVALID_DIGITAL_CHANNEL                     = 0x00000114
PICO_INVALID_DIGITAL_TRIGGER_DIRECTION           = 0x00000115
PICO_SIG_GEN_PRBS_NOT_SUPPORTED                  = 0x00000116
PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS       = 0x00000117
PICO_WARNING_REPEAT_VALUE                        = 0x00000118
PICO_POWER_SUPPLY_CONNECTED                      = 0x00000119
PICO_POWER_SUPPLY_NOT_CONNECTED                  = 0x0000011A
PICO_POWER_SUPPLY_REQUEST_INVALID                = 0x0000011B
PICO_POWER_SUPPLY_UNDERVOLTAGE                   = 0x0000011C
PICO_CAPTURING_DATA                              = 0x0000011D
PICO_USB3_0_DEVICE_NON_USB3_0_PORT               = 0x0000011E
PICO_NOT_SUPPORTED_BY_THIS_DEVICE                = 0x0000011F
PICO_INVALID_DEVICE_RESOLUTION                   = 0x00000120
PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION      = 0x00000121
PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED         = 0x00000122
PICO_SIGGEN_DC_VOLTAGE_NOT_CONFIGURABLE          = 0x00000123
PICO_NO_TRIGGER_ENABLED_FOR_TRIGGER_IN_PRE_TRIG  = 0x00000124
PICO_TRIGGER_WITHIN_PRE_TRIG_NOT_ARMED           = 0x00000125
PICO_TRIGGER_WITHIN_PRE_NOT_ALLOWED_WITH_DELAY   = 0x00000126
PICO_TRIGGER_INDEX_UNAVAILABLE                   = 0x00000127
PICO_AWG_CLOCK_FREQUENCY                         = 0x00000128
PICO_TOO_MANY_CHANNELS_IN_USE                    = 0x00000129
PICO_NULL_CONDITIONS                             = 0x0000012A
PICO_DUPLICATE_CONDITION_SOURCE                  = 0x0000012B
PICO_INVALID_CONDITION_INFO                      = 0x0000012C
PICO_SETTINGS_READ_FAILED                        = 0x0000012D
PICO_SETTINGS_WRITE_FAILED                       = 0x0000012E
PICO_ARGUMENT_OUT_OF_RANGE                       = 0x0000012F
PICO_HARDWARE_VERSION_NOT_SUPPORTED              = 0x00000130
PICO_DIGITAL_HARDWARE_VERSION_NOT_SUPPORTED      = 0x00000131
PICO_ANALOGUE_HARDWARE_VERSION_NOT_SUPPORTED     = 0x00000132
PICO_UNABLE_TO_CONVERT_TO_RESISTANCE             = 0x00000133
PICO_DUPLICATED_CHANNEL                          = 0x00000134
PICO_INVALID_RESISTANCE_CONVERSION               = 0x00000135
PICO_INVALID_VALUE_IN_MAX_BUFFER                 = 0x00000136
PICO_INVALID_VALUE_IN_MIN_BUFFER                 = 0x00000137
PICO_SIGGEN_FREQUENCY_OUT_OF_RANGE               = 0x00000138
PICO_EEPROM2_CORRUPT                             = 0x00000139
PICO_EEPROM2_FAIL                                = 0x0000013A
PICO_SERIAL_BUFFER_TOO_SMALL                     = 0x0000013B
PICO_SIGGEN_TRIGGER_AND_EXTERNAL_CLOCK_CLASH     = 0x0000013C
PICO_WARNING_SIGGEN_AUXIO_TRIGGER_DISABLED       = 0x0000013D
PICO_SIGGEN_GATING_AUXIO_NOT_AVAILABLE           = 0x00000013E
PICO_SIGGEN_GATING_AUXIO_ENABLED                 = 0x00000013F
PICO_RESOURCE_ERROR                              = 0x00000140
PICO_TEMPERATURE_TYPE_INVALID                    = 0x000000141
PICO_TEMPERATURE_TYPE_NOT_SUPPORTED              = 0x000000142
PICO_TIMEOUT                                     = 0x00000143
PICO_DEVICE_NOT_FUNCTIONING                      = 0x00000144
PICO_INTERNAL_ERROR                              = 0x00000145
PICO_MULTIPLE_DEVICES_FOUND                      = 0x00000146
PICO_WARNING_NUMBER_OF_SEGMENTS_REDUCED          = 0x00000147
PICO_CAL_PINS_STATES                             = 0x00000148
PICO_CAL_PINS_FREQUENCY                          = 0x00000149
PICO_CAL_PINS_AMPLITUDE                          = 0x0000014A
PICO_CAL_PINS_WAVETYPE                           = 0x0000014B
PICO_CAL_PINS_OFFSET                             = 0x0000014C
PICO_PROBE_FAULT                                 = 0x0000014D
PICO_PROBE_IDENTITY_UNKNOWN                      = 0x0000014E
PICO_PROBE_POWER_DC_POWER_SUPPLY_REQUIRED        = 0x0000014F
PICO_PROBE_NOT_POWERED_WITH_DC_POWER_SUPPLY      = 0x00000150
PICO_PROBE_CONFIG_FAILURE                        = 0x00000151
PICO_PROBE_INTERACTION_CALLBACK                  = 0x00000152
PICO_UNKNOWN_INTELLIGENT_PROBE                   = 0x00000153
PICO_INTELLIGENT_PROBE_CORRUPT                   = 0x00000154
PICO_PROBE_COLLECTION_NOT_STARTED                = 0x00000155
PICO_PROBE_POWER_CONSUMPTION_EXCEEDED            = 0x00000156
PICO_WARNING_PROBE_CHANNEL_OUT_OF_SYNC           = 0x00000157
PICO_DEVICE_TIME_STAMP_RESET                     = 0x01000000
PICO_WATCHDOGTIMER                               = 0x10000000
PICO_IPP_NOT_FOUND                               = 0x10000001
PICO_IPP_NO_FUNCTION                             = 0x10000002
PICO_IPP_ERROR                                   = 0x10000003
PICO_SHADOW_CAL_NOT_AVAILABLE                    = 0x10000004
PICO_SHADOW_CAL_DISABLED                         = 0x10000005
PICO_SHADOW_CAL_ERROR                            = 0x10000006
PICO_SHADOW_CAL_CORRUPT                          = 0x10000007
PICO_DEVICE_MEMORY_OVERFLOW                      = 0x10000008
PICO_RESERVED_1                                  = 0x11000000

PICO_STATUS                                      = c_uint32


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


# For ps2000 and ps3000
# PS2000Error == PS3000Error so it does not matter which enum we use
ERROR_CODES = {
    PS2000Error.OK: (
        'PICO_OK',
        'PicoTech<model={model}, serial={serial}> is functioning correctly.'
    ),
    PS2000Error.MAX_UNITS_OPENED: (
        'PICO_MAX_UNITS_OPENED',
        'Attempts have been made to open more than {sdk_filename_upper}_MAX_UNITS oscilloscopes.'
    ),
    PS2000Error.MEM_FAIL: (
        'PICO_MEM_FAIL',
        'Not enough memory could be allocated on the host machine.'
    ),
    PS2000Error.NOT_FOUND: (
        'PICO_NOT_FOUND',
        'The PicoTech<model={model}, serial={serial}> could not be found.'
    ),
    PS2000Error.FW_FAIL: (
        'PICO_FW_FAIL',
        'Unable to download firmware.'
    ),
    PS2000Error.NOT_RESPONDING: (
        'PICO_NOT_RESPONDING',
        'The PicoTech<model={model}, serial={serial}> is not responding to commands from the PC.'
    ),
    PS2000Error.CONFIG_FAIL: (
        'PICO_CONFIG_FAIL',
        'The configuration information in the PicoTech<model={model}, serial={serial}> '
        'has become corrupt or is missing.'
    ),
    PS2000Error.OS_NOT_SUPPORTED: (
        'PICO_OS_NOT_SUPPORTED',
        'The operating system is not supported by this driver.'
    ),
    PS2000Error.PICOPP_TOO_OLD: (
        'PICOPP_TOO_OLD',
        'The picopp.sys file is too old to be used with the device driver.'
    ),
}


# for ps####(a)Api
ERROR_CODES_API = {
    PICO_OK: (
        'PICO_OK',
        'PicoTech<model={model}, serial={serial}> is functioning correctly.'
    ),
    PICO_MAX_UNITS_OPENED: (
        'PICO_MAX_UNITS_OPENED',
        'An attempt has been made to open more than {sdk_filename_upper}_MAX_UNITS oscilloscopes.'
    ),
    PICO_MEMORY_FAIL: (
        'PICO_MEMORY_FAIL',
        'Not enough memory could be allocated on the host machine.'
    ),
    PICO_NOT_FOUND: (
        'PICO_NOT_FOUND',
        'The PicoTech<model={model}, serial={serial}> could not be found.'
    ),
    PICO_FW_FAIL: (
        'PICO_FW_FAIL',
        'Unable to download firmware.'
    ),
    PICO_OPEN_OPERATION_IN_PROGRESS: (
        'PICO_OPEN_OPERATION_IN_PROGRESS',
        'The "open_unit" operation is already in progress for PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_OPERATION_FAILED: (
        'PICO_OPERATION_FAILED',
        'The PicoTech<model={model}, serial={serial}> operation failed.'
    ),
    PICO_NOT_RESPONDING: (
        'PICO_NOT_RESPONDING',
        'The PicoTech<model={model}, serial={serial}> is not responding to commands from the PC.'
    ),
    PICO_CONFIG_FAIL: (
        'PICO_CONFIG_FAIL',
        'The configuration information in the PicoTech<model={model}, serial={serial}> has '
        'become corrupt or is missing.'
    ),
    PICO_KERNEL_DRIVER_TOO_OLD: (
        'PICO_KERNEL_DRIVER_TOO_OLD',
        'The picopp.sys file is too old to be used with the device driver.'
    ),
    PICO_EEPROM_CORRUPT: (
        'PICO_EEPROM_CORRUPT',
        'The EEPROM has become corrupt for PicoTech<model={model}, serial={serial}>, so '
        'the device will use a default setting.'
    ),
    PICO_OS_NOT_SUPPORTED: (
        'PICO_OS_NOT_SUPPORTED',
        'The operating system on the PC is not supported by this driver.'
    ),
    PICO_INVALID_HANDLE: (
        'PICO_INVALID_HANDLE',
        'There is no device with the handle value passed.'
    ),
    PICO_INVALID_PARAMETER: (
        'PICO_INVALID_PARAMETER',
        'A parameter value is not valid.'
    ),
    PICO_INVALID_TIMEBASE: (
        'PICO_INVALID_TIMEBASE',
        'The timebase for PicoTech<model={model}, serial={serial}> is not supported or is invalid.'
    ),
    PICO_INVALID_VOLTAGE_RANGE: (
        'PICO_INVALID_VOLTAGE_RANGE',
        'The voltage range for PicoTech<model={model}, serial={serial}> is not supported or is invalid.'
    ),
    PICO_INVALID_CHANNEL: (
        'PICO_INVALID_CHANNEL',
        'The channel number is not valid on PicoTech<model={model}, serial={serial}> or no channels have been set.'
    ),
    PICO_INVALID_TRIGGER_CHANNEL: (
        'PICO_INVALID_TRIGGER_CHANNEL',
        'The channel set for a trigger is not available on PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_INVALID_CONDITION_CHANNEL: (
        'PICO_INVALID_CONDITION_CHANNEL',
        'The channel set for a condition is not available on PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_NO_SIGNAL_GENERATOR: (
        'PICO_NO_SIGNAL_GENERATOR',
        'PicoTech<model={model}, serial={serial}> does not have a signal generator.'
    ),
    PICO_STREAMING_FAILED: (
        'PICO_STREAMING_FAILED',
        'Streaming has failed to start or has stopped without user request.'
    ),
    PICO_BLOCK_MODE_FAILED: (
        'PICO_BLOCK_MODE_FAILED',
        'Block failed to start, a parameter may have been set wrongly.'
    ),
    PICO_NULL_PARAMETER: (
        'PICO_NULL_PARAMETER',
        'A parameter that was required is NULL.'
    ),
    PICO_ETS_MODE_SET: (
        'PICO_ETS_MODE_SET',
        'Function call failed because ETS mode is being used.'
    ),
    PICO_DATA_NOT_AVAILABLE: (
        'PICO_DATA_NOT_AVAILABLE',
        'No data is available from a run_block() call.'
    ),
    PICO_STRING_BUFFER_TOO_SMALL: (
        'PICO_STRING_BUFFER_TOO_SMALL',
        'The buffer passed for the information was too small.'
    ),
    PICO_ETS_NOT_SUPPORTED: (
        'PICO_ETS_NOT_SUPPORTED',
        'ETS is not supported on this device.'
    ),
    PICO_AUTO_TRIGGER_TIME_TOO_SHORT: (
        'PICO_AUTO_TRIGGER_TIME_TOO_SHORT',
        'The auto trigger time is less than the time it will take to collect the pre-trigger data.'
    ),
    PICO_BUFFER_STALL: (
        'PICO_BUFFER_STALL',
        'The collection of data has stalled as unread data would be overwritten.'
    ),
    PICO_TOO_MANY_SAMPLES: (
        'PICO_TOO_MANY_SAMPLES',
        'Number of samples requested is more than available in the current memory segment.'
    ),
    PICO_TOO_MANY_SEGMENTS: (
        'PICO_TOO_MANY_SEGMENTS',
        'Not possible to create number of segments requested.'
    ),
    PICO_PULSE_WIDTH_QUALIFIER: (
        'PICO_PULSE_WIDTH_QUALIFIER',
        'A null pointer has been passed in the trigger function or one of the parameters is out of range.'
    ),
    PICO_DELAY: (
        'PICO_DELAY',
        'One or more of the hold-off parameters are out of range.'
    ),
    PICO_SOURCE_DETAILS: (
        'PICO_SOURCE_DETAILS',
        'One or more of the source details are incorrect.'
    ),
    PICO_CONDITIONS: (
        'PICO_CONDITIONS',
        'One or more of the conditions are incorrect.'
    ),
    PICO_USER_CALLBACK: (
        'PICO_USER_CALLBACK',
        'The driver\'s thread is currently in the {sdk_filename}BlockReady callback function and therefore the '
        'action cannot be carried out.'
    ),
    PICO_DEVICE_SAMPLING: (
        'PICO_DEVICE_SAMPLING',
        'An attempt is being made to get stored data while streaming. Either stop streaming by calling '
        'stop(), or use get_streaming_latest_values().'
    ),
    PICO_NO_SAMPLES_AVAILABLE: (
        'PICO_NO_SAMPLES_AVAILABLE',
        '...because a run has not been completed.'
    ),
    PICO_SEGMENT_OUT_OF_RANGE: (
        'PICO_SEGMENT_OUT_OF_RANGE',
        'The memory index is out of range.'
    ),
    PICO_BUSY: (
        'PICO_BUSY',
        'Data cannot be returned yet.'
    ),
    PICO_STARTINDEX_INVALID: (
        'PICO_STARTINDEX_INVALID',
        'The start time to get stored data is out of range.'
    ),
    PICO_INVALID_INFO: (
        'PICO_INVALID_INFO',
        'The information number requested is not a valid number.'
    ),
    PICO_INFO_UNAVAILABLE: (
        'PICO_INFO_UNAVAILABLE',
        'The handle is invalid so no information is available about the device. '
        'Only PICO_DRIVER_VERSION is available.'
    ),
    PICO_INVALID_SAMPLE_INTERVAL: (
        'PICO_INVALID_SAMPLE_INTERVAL',
        'The sample interval selected for streaming is out of range.'
    ),
    PICO_TRIGGER_ERROR: (
        'PICO_TRIGGER_ERROR',
        'ETS is set but no trigger has been set. A trigger setting is required for ETS.'
    ),
    PICO_MEMORY: (
        'PICO_MEMORY',
        'Driver cannot allocate memory.'
    ),
    PICO_SIG_GEN_PARAM: (
        'PICO_SIG_GEN_PARAM',
        'Incorrect parameter passed to signal generator.'
    ),
    PICO_SHOTS_SWEEPS_WARNING: (
        'PICO_SHOTS_SWEEPS_WARNING',
        'The signal generator will output the signal required but sweeps and shots will be ignored. '
        'Only one parameter can be non-zero.'
    ),
    PICO_SIGGEN_TRIGGER_SOURCE: (
        'PICO_SIGGEN_TRIGGER_SOURCE',
        'A software trigger has been sent but the trigger source is not a software trigger.'
    ),
    PICO_AUX_OUTPUT_CONFLICT: (
        'PICO_AUX_OUTPUT_CONFLICT',
        '{sdk_filename}SetTrigger has found a conflict between the trigger source and the AUXIO output enable.'
    ),
    PICO_AUX_OUTPUT_ETS_CONFLICT: (
        'PICO_AUX_OUTPUT_ETS_CONFLICT',
        'ETS mode is being used and AUXIO is set as an input.'
    ),
    PICO_WARNING_EXT_THRESHOLD_CONFLICT: (
        'PICO_WARNING_EXT_THRESHOLD_CONFLICT',
        'The EXT threshold is being set in both {sdk_filename}SetTrigger function and in the signal '
        'generator but the threshold values differ. The last value set will be used.'
    ),
    PICO_WARNING_AUX_OUTPUT_CONFLICT: (
        'PICO_WARNING_AUX_OUTPUT_CONFLICT',
        'AUX cannot be used as input and output at the same time.'
    ),
    PICO_SIGGEN_OUTPUT_OVER_VOLTAGE: (
        'PICO_SIGGEN_OUTPUT_OVER_VOLTAGE',
        'The combined peak to peak voltage and the analog offset voltage exceed the '
        'allowable voltage the signal generator can produce.'
    ),
    PICO_DELAY_NULL: (
        'PICO_DELAY_NULL',
        'NULL pointer passed as delay parameter.'
    ),
    PICO_INVALID_BUFFER: (
        'PICO_INVALID_BUFFER',
        'The buffers for overview data have not been set while streaming.'
    ),
    PICO_SIGGEN_OFFSET_VOLTAGE: (
        'PICO_SIGGEN_OFFSET_VOLTAGE',
        'The analog offset voltage is out of range.'
    ),
    PICO_SIGGEN_PK_TO_PK: (
        'PICO_SIGGEN_PK_TO_PK',
        'The analog peak to peak voltage is out of range.'
    ),
    PICO_CANCELLED: (
        'PICO_CANCELLED',
        'A block collection has been cancelled.'
    ),
    PICO_SEGMENT_NOT_USED: (
        'PICO_SEGMENT_NOT_USED',
        'The segment index is not currently being used.'
    ),
    PICO_INVALID_CALL: (
        'PICO_INVALID_CALL',
        'The wrong GetValues function has been called for the collection mode in use.'
    ),
    PICO_GET_VALUES_INTERRUPTED: (
        'PICO_GET_VALUES_INTERRUPTED',
        'The GetValues function has interrupted.'
    ),
    PICO_NOT_USED: (
        'PICO_NOT_USED',
        'The function is not available.'
    ),
    PICO_INVALID_SAMPLERATIO: (
        'PICO_INVALID_SAMPLERATIO',
        'The aggregation ratio requested is out of range.'
    ),
    PICO_INVALID_STATE: (
        'PICO_INVALID_STATE',
        'PicoTech<model={model}, serial={serial}> is in an invalid state.'
    ),
    PICO_NOT_ENOUGH_SEGMENTS: (
        'PICO_NOT_ENOUGH_SEGMENTS',
        'The number of segments allocated is fewer than the number of captures requested.'
    ),
    PICO_DRIVER_FUNCTION: (
        'PICO_DRIVER_FUNCTION',
        'You called a driver function while another driver function was still being processed.'
    ),
    PICO_RESERVED: (
        'PICO_RESERVED',
        'Reserved.'
    ),
    PICO_INVALID_COUPLING: (
        'PICO_INVALID_COUPLING',
        'An invalid coupling type was specified in {sdk_filename}SetChannel.'
    ),
    PICO_BUFFERS_NOT_SET: (
        'PICO_BUFFERS_NOT_SET',
        'An attempt was made to get data before a data buffer was defined.'
    ),
    PICO_RATIO_MODE_NOT_SUPPORTED: (
        'PICO_RATIO_MODE_NOT_SUPPORTED',
        'The selected down-sampling mode (used for data reduction) is not allowed.'
    ),
    PICO_RAPID_NOT_SUPPORT_AGGREGATION: (
        'PICO_RAPID_NOT_SUPPORT_AGGREGATION',
        'RapidBlock mode does not support aggregation.'
    ),
    PICO_INVALID_TRIGGER_PROPERTY: (
        'PICO_INVALID_TRIGGER_PROPERTY',
        'An invalid parameter was passed to {sdk_filename}SetTriggerChannelProperties.'
    ),
    PICO_INTERFACE_NOT_CONNECTED: (
        'PICO_INTERFACE_NOT_CONNECTED',
        'The driver was unable to contact the oscilloscope.'
    ),
    PICO_RESISTANCE_AND_PROBE_NOT_ALLOWED: (
        'PICO_RESISTANCE_AND_PROBE_NOT_ALLOWED',
        'The resistance and probe are not allowed.'
    ),
    PICO_POWER_FAILED: (
        'PICO_POWER_FAILED',
        'Power failure.'
    ),
    PICO_SIGGEN_WAVEFORM_SETUP_FAILED: (
        'PICO_SIGGEN_WAVEFORM_SETUP_FAILED',
        'A problem occurred in {sdk_filename}SetSigGenBuiltIn or {sdk_filename}SetSigGenArbitrary.'
    ),
    PICO_FPGA_FAIL: (
        'PICO_FPGA_FAIL',
        ''
    ),
    PICO_POWER_MANAGER: (
        'PICO_POWER_MANAGER',
        ''
    ),
    PICO_INVALID_ANALOGUE_OFFSET: (
        'PICO_INVALID_ANALOGUE_OFFSET',
        'An impossible analogue offset value was specified in {sdk_filename}SetChannel.'
    ),
    PICO_PLL_LOCK_FAILED: (
        'PICO_PLL_LOCK_FAILED',
        'Unable to configure the PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_ANALOG_BOARD: (
        'PICO_ANALOG_BOARD',
        'The oscilloscope\'s analog board is not detected, or is not connected to the digital board.'
    ),
    PICO_CONFIG_FAIL_AWG: (
        'PICO_CONFIG_FAIL_AWG',
        'Unable to configure the signal generator.'
    ),
    PICO_INITIALISE_FPGA: (
        'PICO_INITIALISE_FPGA',
        'The FPGA cannot be initialized, so unit cannot be opened.'
    ),
    PICO_EXTERNAL_FREQUENCY_INVALID: (
        'PICO_EXTERNAL_FREQUENCY_INVALID',
        'The frequency for the external clock is not within 5% of the stated value.'
    ),
    PICO_CLOCK_CHANGE_ERROR: (
        'PICO_CLOCK_CHANGE_ERROR',
        'The FPGA could not lock the clock signal.'
    ),
    PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH: (
        'PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH',
        'You are trying to configure the AUX input as both a trigger and a reference clock.'
    ),
    PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH: (
        'PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH',
        'You are trying to configure the AUX input as both a pulse width qualifier and a reference clock.'
    ),
    PICO_UNABLE_TO_OPEN_SCALING_FILE: (
        'PICO_UNABLE_TO_OPEN_SCALING_FILE',
        'The scaling file set can not be opened.'
    ),
    PICO_MEMORY_CLOCK_FREQUENCY: (
        'PICO_MEMORY_CLOCK_FREQUENCY',
        'The frequency of the memory is reporting incorrectly.'
    ),
    PICO_I2C_NOT_RESPONDING: (
        'PICO_I2C_NOT_RESPONDING',
        'The I2C that is being actioned is not responding to requests.'
    ),
    PICO_NO_CAPTURES_AVAILABLE: (
        'PICO_NO_CAPTURES_AVAILABLE',
        'There are no captures available and therefore no data can be returned.'
    ),
    PICO_NOT_USED_IN_THIS_CAPTURE_MODE: (
        'PICO_NOT_USED_IN_THIS_CAPTURE_MODE',
        'The capture mode the device is currently running in does not support the current request.'
    ),
    PICO_GET_DATA_ACTIVE: (
        'PICO_GET_DATA_ACTIVE',
        'Reserved'
    ),
    PICO_IP_NETWORKED: (
        'PICO_IP_NETWORKED',
        'PicoTech<model={model}, serial={serial}> is currently connected via the IP '
        'Network socket and thus the call made is not supported.'
    ),
    PICO_INVALID_IP_ADDRESS: (
        'PICO_INVALID_IP_ADDRESS',
        'An IP address that is not correct has been passed to the driver.'
    ),
    PICO_IPSOCKET_FAILED: (
        'PICO_IPSOCKET_FAILED',
        'The IP socket has failed.'
    ),
    PICO_IPSOCKET_TIMEDOUT: (
        'PICO_IPSOCKET_TIMEDOUT',
        'The IP socket has timed out.'
    ),
    PICO_SETTINGS_FAILED: (
        'PICO_SETTINGS_FAILED',
        'The settings requested have failed to be set.'
    ),
    PICO_NETWORK_FAILED: (
        'PICO_NETWORK_FAILED',
        'The network connection has failed.'
    ),
    PICO_WS2_32_DLL_NOT_LOADED: (
        'PICO_WS2_32_DLL_NOT_LOADED',
        'Unable to load the WS2 dll.'
    ),
    PICO_INVALID_IP_PORT: (
        'PICO_INVALID_IP_PORT',
        'The IP port is invalid.'
    ),
    PICO_COUPLING_NOT_SUPPORTED: (
        'PICO_COUPLING_NOT_SUPPORTED',
        'The type of coupling requested is not supported on the opened device.'
    ),
    PICO_BANDWIDTH_NOT_SUPPORTED: (
        'PICO_BANDWIDTH_NOT_SUPPORTED',
        'Bandwidth limit is not supported on PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_INVALID_BANDWIDTH: (
        'PICO_INVALID_BANDWIDTH',
        'The value requested for the bandwidth limit is out of range.'
    ),
    PICO_AWG_NOT_SUPPORTED: (
        'PICO_AWG_NOT_SUPPORTED',
        'PicoTech<model={model}, serial={serial}> does not have an arbitrary waveform generator.'
    ),
    PICO_ETS_NOT_RUNNING: (
        'PICO_ETS_NOT_RUNNING',
        'Data has been requested with ETS mode set but run_block() has not been called, or stop() has been called.'
    ),
    PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED: (
        'PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED',
        'White noise is not supported on PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED: (
        'PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED',
        'The wave type requested is not supported by PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_INVALID_DIGITAL_PORT: (
        'PICO_INVALID_DIGITAL_PORT',
        'The digital port number is invalid.'
    ),
    PICO_INVALID_DIGITAL_CHANNEL: (
        'PICO_INVALID_DIGITAL_CHANNEL',
        'The digital channel is invalid.'
    ),
    PICO_INVALID_DIGITAL_TRIGGER_DIRECTION: (
        'PICO_INVALID_DIGITAL_TRIGGER_DIRECTION',
        'The digital trigger direction is not a valid trigger direction.'
    ),
    PICO_SIG_GEN_PRBS_NOT_SUPPORTED: (
        'PICO_SIG_GEN_PRBS_NOT_SUPPORTED',
        'Siggen does not generate pseudo random bit stream.'
    ),
    PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS: (
        'PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS',
        'When a digital port is enabled, ETS sample mode is not available for use.'
    ),
    PICO_WARNING_REPEAT_VALUE: (
        'PICO_WARNING_REPEAT_VALUE',
        'Not applicable to PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_POWER_SUPPLY_CONNECTED: (
        'PICO_POWER_SUPPLY_CONNECTED',
        'The DC power supply is connected for PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_POWER_SUPPLY_NOT_CONNECTED: (
        'PICO_POWER_SUPPLY_NOT_CONNECTED',
        "The DC power supply isn't connected for PicoTech<model={model}, serial={serial}>."
    ),
    PICO_POWER_SUPPLY_REQUEST_INVALID: (
        'PICO_POWER_SUPPLY_REQUEST_INVALID',
        'Incorrect power mode passed for current power source.'
    ),
    PICO_POWER_SUPPLY_UNDERVOLTAGE: (
        'PICO_POWER_SUPPLY_UNDERVOLTAGE',
        'The supply voltage from the USB source is too low for PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_CAPTURING_DATA: (
        'PICO_CAPTURING_DATA',
        'PicoTech<model={model}, serial={serial}> is currently busy capturing data.'
    ),
    PICO_USB3_0_DEVICE_NON_USB3_0_PORT: (
        'PICO_USB3_0_DEVICE_NON_USB3_0_PORT',
        'A USB 3.0 device is connected to a non-USB 3.0 port.'
    ),
    PICO_NOT_SUPPORTED_BY_THIS_DEVICE: (
        'PICO_NOT_SUPPORTED_BY_THIS_DEVICE',
        'A function has been called that is not supported by PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_INVALID_DEVICE_RESOLUTION: (
        'PICO_INVALID_DEVICE_RESOLUTION',
        'The resolution for PicoTech<model={model}, serial={serial}> is invalid (out of range).'
    ),
    PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION: (
        'PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION',
        'The number of channels which can be enabled is limited in 15 and 16-bit modes.'
    ),
    PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED: (
        'PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED',
        'USB Power not sufficient to power all channels on PicoTech<model={model}, serial={serial}>.'
    ),
    PICO_SIGGEN_DC_VOLTAGE_NOT_CONFIGURABLE: (
        'PICO_SIGGEN_DC_VOLTAGE_NOT_CONFIGURABLE',
        ''
    ),
    PICO_NO_TRIGGER_ENABLED_FOR_TRIGGER_IN_PRE_TRIG: (
        'PICO_NO_TRIGGER_ENABLED_FOR_TRIGGER_IN_PRE_TRIG',
        ''
    ),
    PICO_TRIGGER_WITHIN_PRE_TRIG_NOT_ARMED: (
        'PICO_TRIGGER_WITHIN_PRE_TRIG_NOT_ARMED',
        ''
    ),
    PICO_TRIGGER_WITHIN_PRE_NOT_ALLOWED_WITH_DELAY: (
        'PICO_TRIGGER_WITHIN_PRE_NOT_ALLOWED_WITH_DELAY',
        ''
    ),
    PICO_TRIGGER_INDEX_UNAVAILABLE: (
        'PICO_TRIGGER_INDEX_UNAVAILABLE',
        ''
    ),
    PICO_AWG_CLOCK_FREQUENCY: (
        'PICO_AWG_CLOCK_FREQUENCY',
        ''
    ),
    PICO_TOO_MANY_CHANNELS_IN_USE: (
        'PICO_TOO_MANY_CHANNELS_IN_USE',
        'There are more than 4 analogue channels with a trigger condition set.'
    ),
    PICO_NULL_CONDITIONS: (
        'PICO_NULL_CONDITIONS',
        ''
    ),
    PICO_DUPLICATE_CONDITION_SOURCE: (
        'PICO_DUPLICATE_CONDITION_SOURCE',
        ''
    ),
    PICO_INVALID_CONDITION_INFO: (
        'PICO_INVALID_CONDITION_INFO',
        ''
    ),
    PICO_SETTINGS_READ_FAILED: (
        'PICO_SETTINGS_READ_FAILED',
        ''
    ),
    PICO_SETTINGS_WRITE_FAILED: (
        'PICO_SETTINGS_WRITE_FAILED',
        ''
    ),
    PICO_ARGUMENT_OUT_OF_RANGE: (
        'PICO_ARGUMENT_OUT_OF_RANGE',
        ''
    ),
    PICO_HARDWARE_VERSION_NOT_SUPPORTED: (
        'PICO_HARDWARE_VERSION_NOT_SUPPORTED',
        ''
    ),
    PICO_DIGITAL_HARDWARE_VERSION_NOT_SUPPORTED: (
        'PICO_DIGITAL_HARDWARE_VERSION_NOT_SUPPORTED',
        ''
    ),
    PICO_ANALOGUE_HARDWARE_VERSION_NOT_SUPPORTED: (
        'PICO_ANALOGUE_HARDWARE_VERSION_NOT_SUPPORTED',
        ''
    ),
    PICO_UNABLE_TO_CONVERT_TO_RESISTANCE: (
        'PICO_ANALOGUE_HARDWARE_VERSION_NOT_SUPPORTED',
        ''
    ),
    PICO_DUPLICATED_CHANNEL: (
        'PICO_DUPLICATED_CHANNEL',
        ''
    ),
    PICO_INVALID_RESISTANCE_CONVERSION: (
        'PICO_INVALID_RESISTANCE_CONVERSION',
        ''
    ),
    PICO_INVALID_VALUE_IN_MAX_BUFFER: (
        'PICO_INVALID_VALUE_IN_MAX_BUFFER',
        ''
    ),
    PICO_INVALID_VALUE_IN_MIN_BUFFER: (
        'PICO_INVALID_VALUE_IN_MIN_BUFFER',
        ''
    ),
    PICO_SIGGEN_FREQUENCY_OUT_OF_RANGE: (
        'PICO_SIGGEN_FREQUENCY_OUT_OF_RANGE',
        ''
    ),
    PICO_EEPROM2_CORRUPT: (
        'PICO_EEPROM2_CORRUPT',
        ''
    ),
    PICO_EEPROM2_FAIL: (
        'PICO_EEPROM2_FAIL',
        ''
    ),
    PICO_SERIAL_BUFFER_TOO_SMALL: (
        'PICO_SERIAL_BUFFER_TOO_SMALL',
        'The serial buffer is too small for the required information.'
    ),
    PICO_SIGGEN_TRIGGER_AND_EXTERNAL_CLOCK_CLASH: (
        'PICO_SIGGEN_TRIGGER_AND_EXTERNAL_CLOCK_CLASH',
        'The signal generator trigger and the external clock have both been set.'
    ),
    PICO_WARNING_SIGGEN_AUXIO_TRIGGER_DISABLED: (
        'PICO_WARNING_SIGGEN_AUXIO_TRIGGER_DISABLED',
        'The AUX trigger was enabled and the external clock has been enabled, so the AUX has been automatically disabled.'
    ),
    PICO_SIGGEN_GATING_AUXIO_NOT_AVAILABLE: (
        'PICO_SIGGEN_GATING_AUXIO_NOT_AVAILABLE',
        'The AUX I/O was set as a scope trigger and is now being set as a signal generator gating trigger.'
    ),
    PICO_SIGGEN_GATING_AUXIO_ENABLED: (
        'PICO_SIGGEN_GATING_AUXIO_ENABLED',
        'The AUX I/O was set by the signal generator as a gating trigger and is now being set as a scope trigger.'
    ),
    PICO_RESOURCE_ERROR: (
        'PICO_RESOURCE_ERROR',
        'A resource has failed to initialise.'
    ),
    PICO_TEMPERATURE_TYPE_INVALID: (
        'PICO_TEMPERATURE_TYPE_INVALID',
        'The temperature type is out of range.'
    ),
    PICO_TEMPERATURE_TYPE_NOT_SUPPORTED: (
        'PICO_TEMPERATURE_TYPE_NOT_SUPPORTED',
        'A requested temperature type is not supported on this device.'
    ),
    PICO_TIMEOUT: (
        'PICO_TIMEOUT',
        'A read/write to the device has timed out.'
    ),
    PICO_DEVICE_NOT_FUNCTIONING: (
        'PICO_DEVICE_NOT_FUNCTIONING',
        'The device cannot be connected correctly.'
    ),
    PICO_INTERNAL_ERROR: (
        'PICO_INTERNAL_ERROR',
        'The driver has experienced an unknown error and is unable to recover from this error.'
    ),
    PICO_MULTIPLE_DEVICES_FOUND: (
        'PICO_MULTIPLE_DEVICES_FOUND',
        'Used when opening units via IP and more than multiple units have the same ip address.'
    ),
    PICO_WARNING_NUMBER_OF_SEGMENTS_REDUCED: (
        'PICO_WARNING_NUMBER_OF_SEGMENTS_REDUCED',
        'The number of segments has been reduced.'
    ),
    PICO_CAL_PINS_STATES: (
        'PICO_CAL_PINS_STATES',
        'The calibration pin states argument is out of range.'
    ),
    PICO_CAL_PINS_FREQUENCY: (
        'PICO_CAL_PINS_FREQUENCY',
        'The calibration pin frequency argument is out of range.'
    ),
    PICO_CAL_PINS_AMPLITUDE: (
        'PICO_CAL_PINS_AMPLITUDE',
        'The calibration pin amplitude argument is out of range.'
    ),
    PICO_CAL_PINS_WAVETYPE: (
        'PICO_CAL_PINS_WAVETYPE',
        'The calibration pin wavetype argument is out of range.'
    ),
    PICO_CAL_PINS_OFFSET: (
        'PICO_CAL_PINS_OFFSET',
        'The calibration pin offset argument is out of range.'
    ),
    PICO_PROBE_FAULT: (
        'PICO_PROBE_FAULT',
        'The probe\'s identity has a problem.'
    ),
    PICO_PROBE_IDENTITY_UNKNOWN: (
        'PICO_PROBE_IDENTITY_UNKNOWN',
        'The probe has not been identified.'
    ),
    PICO_PROBE_POWER_DC_POWER_SUPPLY_REQUIRED: (
        'PICO_PROBE_POWER_DC_POWER_SUPPLY_REQUIRED',
        'Enabling the probe would cause the device to exceed the allowable current limit.'
    ),
    PICO_PROBE_NOT_POWERED_WITH_DC_POWER_SUPPLY: (
        'PICO_PROBE_NOT_POWERED_WITH_DC_POWER_SUPPLY',
        'The DC power supply is connected; enabling the probe would cause the device to exceed the allowable current limit.'
    ),
    PICO_PROBE_CONFIG_FAILURE: (
        'PICO_PROBE_CONFIG_FAILURE',
        'Failed to complete probe configuration.'
    ),
    PICO_PROBE_INTERACTION_CALLBACK: (
        'PICO_PROBE_INTERACTION_CALLBACK',
        'Failed to set the callback function, as currently in current callback function.'
    ),
    PICO_UNKNOWN_INTELLIGENT_PROBE: (
        'PICO_UNKNOWN_INTELLIGENT_PROBE',
        'The probe has been verified but not know on this driver.'
    ),
    PICO_INTELLIGENT_PROBE_CORRUPT: (
        'PICO_INTELLIGENT_PROBE_CORRUPT',
        'The intelligent probe cannot be verified.'
    ),
    PICO_PROBE_COLLECTION_NOT_STARTED: (
        'PICO_PROBE_COLLECTION_NOT_STARTED',
        'The callback is null, probe collection will only start when first callback is a none null pointer.'
    ),
    PICO_PROBE_POWER_CONSUMPTION_EXCEEDED: (
        'PICO_PROBE_POWER_CONSUMPTION_EXCEEDED',
        'The current drawn by the probe(s) has exceeded the allowed limit.'
    ),
    PICO_WARNING_PROBE_CHANNEL_OUT_OF_SYNC: (
        'PICO_WARNING_PROBE_CHANNEL_OUT_OF_SYNC',
        'The channel range limits have changed due to connecting or disconnecting a probe the channel has been enabled.'
    ),
    PICO_DEVICE_TIME_STAMP_RESET: (
        'PICO_DEVICE_TIME_STAMP_RESET',
        ''
    ),
    PICO_WATCHDOGTIMER: (
        'PICO_WATCHDOGTIMER',
        ''
    ),
    PICO_IPP_NOT_FOUND: (
        'PICO_IPP_NOT_FOUND',
        'The picoipp.dll has not been found.'
    ),
    PICO_IPP_NO_FUNCTION: (
        'PICO_IPP_NO_FUNCTION',
        'A function in the picoipp.dll does not exist.'
    ),
    PICO_IPP_ERROR: (
        'PICO_IPP_ERROR',
        'The Pico IPP call has failed.'
    ),
    PICO_SHADOW_CAL_NOT_AVAILABLE: (
        'PICO_SHADOW_CAL_NOT_AVAILABLE',
        'Shadow calibration is not available on this device.'
    ),
    PICO_SHADOW_CAL_DISABLED: (
        'PICO_SHADOW_CAL_DISABLED',
        'Shadow calibration is currently disabled.'
    ),
    PICO_SHADOW_CAL_ERROR: (
        'PICO_SHADOW_CAL_ERROR',
        'Shadow calibration error has occurred.'
    ),
    PICO_SHADOW_CAL_CORRUPT: (
        'PICO_SHADOW_CAL_CORRUPT',
        'The shadow calibration is corrupt.'
    ),
    PICO_DEVICE_MEMORY_OVERFLOW: (
        'PICO_DEVICE_MEMORY_OVERFLOW',
        'The onboard memory the of device has overflowed.'
    ),
}

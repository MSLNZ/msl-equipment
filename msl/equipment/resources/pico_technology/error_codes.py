"""
Exceptions and error codes.
"""
from ctypes import c_uint32
c_enum = c_uint32


class PicoScopeError(Exception):
    pass

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
PICO_DEVICE_TIME_STAMP_RESET                     = 0x01000000
PICO_WATCHDOGTIMER                               = 0x10000000

PICO_STATUS                                      = c_uint32

PICO_MAC_ADDRESS                                 = 0x0000000B


# for ps2000 and ps3000
ERROR_CODES = {
    0: ('PICO_OK',
        'PicoScope<model={model}, serial={serial}> is functioning correctly.'),
    1: ('PICO_MAX_UNITS_OPENED',
        'Attempts have been made to open more than {sdk_filename_upper}_MAX_UNITS oscilloscopes.'),
    2: ('PICO_MEM_FAIL',
        'Not enough memory could be allocated on the host machine.'),
    3: ('PICO_NOT_FOUND',
        'The PicoScope<model={model}, serial={serial}> could not be found.'),
    4: ('PICO_FW_FAIL',
        'Unable to download firmware.'),
    5: ('PICO_NOT_RESPONDING',
        'The PicoScope<model={model}, serial={serial}> is not responding to '
        'commands from the PC.'),
    6: ('PICO_CONFIG_FAIL',
        'The configuration information in the PicoScope<model={model}, serial={serial}> '
        'has become corrupt or is missing.'),
    7: ('PICO_OS_NOT_SUPPORTED',
        'The operating system is not supported by this driver.'),
}


# for ps####(a)Api
ERROR_CODES_API = {
    PICO_OK: (
        'PICO_OK',
        'PicoScope<model={model}, serial={serial}> is functioning correctly.'
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
        'The PicoScope<model={model}, serial={serial}> could not be found.'
    ),
    PICO_FW_FAIL: (
        'PICO_FW_FAIL',
        'Unable to download firmware.'
    ),
    PICO_OPEN_OPERATION_IN_PROGRESS: (
        'PICO_OPEN_OPERATION_IN_PROGRESS',
        'The "open_unit" operation is already in progress for PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_OPERATION_FAILED: (
        'PICO_OPERATION_FAILED',
        'The PicoScope<model={model}, serial={serial}> operation failed.'
    ),
    PICO_NOT_RESPONDING: (
        'PICO_NOT_RESPONDING',
        'The PicoScope<model={model}, serial={serial}> is not responding to commands from the PC.'
    ),
    PICO_CONFIG_FAIL: (
        'PICO_CONFIG_FAIL',
        'The configuration information in the PicoScope<model={model}, serial={serial}> has '
        'become corrupt or is missing.'
    ),
    PICO_KERNEL_DRIVER_TOO_OLD: (
        'PICO_KERNEL_DRIVER_TOO_OLD',
        'The picopp.sys file is too old to be used with the device driver.'
    ),
    PICO_EEPROM_CORRUPT: (
        'PICO_EEPROM_CORRUPT',
        'The EEPROM has become corrupt for PicoScope<model={model}, serial={serial}>, so '
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
        'The timebase for PicoScope<model={model}, serial={serial}> is not supported or is invalid.'
    ),
    PICO_INVALID_VOLTAGE_RANGE: (
        'PICO_INVALID_VOLTAGE_RANGE',
        'The voltage range for PicoScope<model={model}, serial={serial}> is not supported or is invalid.'
    ),
    PICO_INVALID_CHANNEL: (
        'PICO_INVALID_CHANNEL',
        'The channel number is not valid on PicoScope<model={model}, serial={serial}> or no channels have been set.'
    ),
    PICO_INVALID_TRIGGER_CHANNEL: (
        'PICO_INVALID_TRIGGER_CHANNEL',
        'The channel set for a trigger is not available on PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_INVALID_CONDITION_CHANNEL: (
        'PICO_INVALID_CONDITION_CHANNEL',
        'The channel set for a condition is not available on PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_NO_SIGNAL_GENERATOR: (
        'PICO_NO_SIGNAL_GENERATOR',
        'PicoScope<model={model}, serial={serial}> does not have a signal generator.'
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
    PICO_MEMORY: (
        'PICO_MEMORY',
        'Driver cannot allocate memory.'
    ),
    PICO_SIG_GEN_PARAM: (
        'PICO_SIG_GEN_PARAM',
        'Incorrect parameter passed to signal generator.'
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
        'PicoScope<model={model}, serial={serial}> is in an invalid state.'
    ),
    PICO_NOT_ENOUGH_SEGMENTS: (
        'PICO_NOT_ENOUGH_SEGMENTS',
        'The number of segments allocated is fewer than the number of captures requested.'
    ),
    PICO_DRIVER_FUNCTION: (
        'PICO_DRIVER_FUNCTION',
        'You called a driver function while another driver function was still being processed.'
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
    PICO_INVALID_TRIGGER_PROPERTY: (
        'PICO_INVALID_TRIGGER_PROPERTY',
        'An invalid parameter was passed to {sdk_filename}SetTriggerChannelProperties.'
    ),
    PICO_INTERFACE_NOT_CONNECTED: (
        'PICO_INTERFACE_NOT_CONNECTED',
        'The driver was unable to contact the oscilloscope.'
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
        'Unable to configure the PicoScope<model={model}, serial={serial}>.'
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
        'The frequency for the external clock is not within ±5% of the stated value.'
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
        'PicoScope<model={model}, serial={serial}> is currently connected via the IP '
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
        'Bandwidth limit is not supported on PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_INVALID_BANDWIDTH: (
        'PICO_INVALID_BANDWIDTH',
        'The value requested for the bandwidth limit is out of range.'
    ),
    PICO_AWG_NOT_SUPPORTED: (
        'PICO_AWG_NOT_SUPPORTED',
        'PicoScope<model={model}, serial={serial}> does not have an arbitrary waveform generator.'
    ),
    PICO_ETS_NOT_RUNNING: (
        'PICO_ETS_NOT_RUNNING',
        'Data has been requested with ETS mode set but run_block() has not been called, or stop() has been called.'
    ),
    PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED: (
        'PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED',
        'White noise is not supported on PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED: (
        'PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED',
        'The wave type requested is not supported by PicoScope<model={model}, serial={serial}>.'
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
        'Not applicable to PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_POWER_SUPPLY_CONNECTED: (
        'PICO_POWER_SUPPLY_CONNECTED',
        'The DC power supply is connected for PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_POWER_SUPPLY_NOT_CONNECTED: (
        'PICO_POWER_SUPPLY_NOT_CONNECTED',
        'The DC power supply isn’t connected for PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_POWER_SUPPLY_REQUEST_INVALID: (
        'PICO_POWER_SUPPLY_REQUEST_INVALID',
        'Incorrect power mode passed for current power source.'
    ),
    PICO_POWER_SUPPLY_UNDERVOLTAGE: (
        'PICO_POWER_SUPPLY_UNDERVOLTAGE',
        'The supply voltage from the USB source is too low for PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_CAPTURING_DATA: (
        'PICO_CAPTURING_DATA',
        'PicoScope<model={model}, serial={serial}> is currently busy capturing data.'
    ),
    PICO_NOT_SUPPORTED_BY_THIS_DEVICE: (
        'PICO_NOT_SUPPORTED_BY_THIS_DEVICE',
        'A function has been called that is not supported by PicoScope<model={model}, serial={serial}>.'
    ),
    PICO_INVALID_DEVICE_RESOLUTION: (
        'PICO_INVALID_DEVICE_RESOLUTION',
        'The resolution for PicoScope<model={model}, serial={serial}> is invalid (out of range).'
    ),
    PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION: (
        'PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION',
        'The number of channels which can be enabled is limited in 15 and 16-bit modes.'
    ),
    PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED: (
        'PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED',
        'USB Power not sufficient to power all channels on PicoScope<model={model}, serial={serial}>.'
    ),
}

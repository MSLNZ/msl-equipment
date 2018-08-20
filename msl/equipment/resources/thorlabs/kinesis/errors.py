"""
Device and Low Level Error Codes defined in Thorlabs Kinesis v1.14.10
"""

FT_OK                         = 0x00
FT_InvalidHandle              = 0x01
FT_DeviceNotFound             = 0x02
FT_DeviceNotOpened            = 0x03
FT_IOError                    = 0x04
FT_InsufficientResources      = 0x05
FT_InvalidParameter           = 0x06
FT_DeviceNotPresent           = 0x07
FT_IncorrectDevice            = 0x08

FT_NoDLLLoaded                = 0x10
FT_NoFunctionsAvailable       = 0x11
FT_FunctionNotAvailable       = 0x12
FT_BadFunctionPointer         = 0x13
FT_GenericFunctionFail        = 0x14
FT_SpecificFunctionFail       = 0x15

TL_ALREADY_OPEN               = 0x20
TL_NO_RESPONSE                = 0x21
TL_NOT_IMPLEMENTED            = 0x22
TL_FAULT_REPORTED             = 0x23
TL_INVALID_OPERATION          = 0x24
TL_DISCONNECTING              = 0x28
TL_FIRMWARE_BUG               = 0x29
TL_INITIALIZATION_FAILURE     = 0x2A
TL_INVALID_CHANNEL            = 0x2B

TL_UNHOMED                    = 0x25
TL_INVALID_POSITION           = 0x26
TL_INVALID_VELOCITY_PARAMETER = 0x27
TL_CANNOT_HOME_DEVICE         = 0x2C
TL_JOG_CONTINOUS_MODE         = 0x2D
TL_NO_MOTOR_INFO              = 0x2E
TL_CMD_TEMP_UNAVAILABLE       = 0x2F

ERROR_CODES = {
    FT_OK: (
        'FT_OK',
        'Success'
    ),
    FT_InvalidHandle: (
        'FT_InvalidHandle',
        'The FTDI functions have not been initialized'
    ),
    FT_DeviceNotFound: (
        'FT_DeviceNotFound',
        'The device could not be found. This can be generated if the function '
        'MotionControl.build_device_list() has not been called'
    ),
    FT_DeviceNotOpened: (
        'FT_DeviceNotOpened',
        'The device must be opened before it can be accessed. See the appropriate '
        'open() function for your device'
    ),
    FT_IOError: (
        'FT_IOError',
        'An I/O Error has occurred in the FTDI chip'
    ),
    FT_InsufficientResources: (
        'FT_InsufficientResources',
        'There are insufficient resources to run this application'
    ),
    FT_InvalidParameter: (
        'FT_InvalidParameter',
        'An invalid parameter has been supplied to the device'
    ),
    FT_DeviceNotPresent: (
        'FT_DeviceNotPresent',
        'The device is no longer present, it may have been disconnected since the '
        'last MotionControl.build_device_list() call'
    ),
    FT_IncorrectDevice: (
        'FT_IncorrectDevice',
        'The device detected does not match that expected'
    ),
    FT_NoDLLLoaded: (
        'FT_NoDLLLoaded',
        'The library for this device could not be found'
    ),
    FT_NoFunctionsAvailable: (
        'FT_NoFunctionsAvailable',
        'No functions available for this device'
    ),
    FT_FunctionNotAvailable: (
        'FT_FunctionNotAvailable',
        'The function is not available for this device'
    ),
    FT_BadFunctionPointer: (
        'FT_BadFunctionPointer',
        'Bad function pointer detected'
    ),
    FT_GenericFunctionFail: (
        'FT_GenericFunctionFail',
        'The function failed to complete succesfully'
    ),
    FT_SpecificFunctionFail: (
        'FT_SpecificFunctionFail',
        'The function failed to complete succesfully'
    ),
    TL_ALREADY_OPEN: (
        'TL_ALREADY_OPEN',
        'Attempt to open a device that was already open'
    ),
    TL_NO_RESPONSE: (
        'TL_NO_RESPONSE',
        'The device has stopped responding'
    ),
    TL_NOT_IMPLEMENTED: (
        'TL_NOT_IMPLEMENTED',
        'This function has not been implemented'
    ),
    TL_FAULT_REPORTED: (
        'TL_FAULT_REPORTED',
        'The device has reported a fault'
    ),
    TL_INVALID_OPERATION: (
        'TL_INVALID_OPERATION',
        'The function could not be completed at this time'
    ),
    TL_DISCONNECTING: (
        'TL_DISCONNECTING',
        'The function could not be completed because the device is disconnected'
    ),
    TL_FIRMWARE_BUG: (
        'TL_FIRMWARE_BUG',
        'The firmware has thrown an error'
    ),
    TL_INITIALIZATION_FAILURE: (
        'TL_INITIALIZATION_FAILURE',
        'The device has failed to initialize'
    ),
    TL_INVALID_CHANNEL: (
        'TL_INVALID_CHANNEL',
        'An Invalid channel address was supplied'
    ),
    TL_UNHOMED: (
        'TL_UNHOMED',
        'The device cannot perform this function until it has been Homed'
    ),
    TL_INVALID_POSITION: (
        'TL_INVALID_POSITION',
        'The function cannot be performed as it would result in an illegal position'
    ),
    TL_INVALID_VELOCITY_PARAMETER: (
        'TL_INVALID_VELOCITY_PARAMETER',
        'An invalid velocity parameter was supplied. The velocity must be greater than zero'
    ),
    TL_CANNOT_HOME_DEVICE: (
        'TL_CANNOT_HOME_DEVICE',
        'This device does not support Homing. Check the Limit switch parameters are correct'
    ),
    TL_JOG_CONTINOUS_MODE: (
        'TL_JOG_CONTINOUS_MODE',
        'An invalid jog mode was supplied for the jog function'
    ),
    TL_NO_MOTOR_INFO: (
        'TL_NO_MOTOR_INFO',
        'There is no Motor Parameters available to convert Real World Units'
    ),
    TL_CMD_TEMP_UNAVAILABLE: (
        'TL_CMD_TEMP_UNAVAILABLE',
        'Command temporarily unavailable, Device may be busy'
    )
}

"""Wrapper around the `avaspec` SDK from [Avantes](https://www.avantes.com/){:target="_blank"}."""

# cSpell: ignore Sens CalibConvers Fiber Nmsr Resp Prescan Multifactor Navg nmax INTTIME
# cSpell: ignore WINFUNCTYPE MEASPARAM FWVER MILLI WAVELEN NONLIN ANALOG NOMON NOCONNECTION
# cSpell: ignore DYNDARK FPGA STARTPIXEL ENDPIXEL STARTPIX ENDPIX MFACTOR USBMINI HAMG VUSB WPARM LPARM
from __future__ import annotations

import sys
from ctypes import (
    POINTER,
    Structure,
    c_bool,
    c_char,
    c_char_p,
    c_double,
    c_float,
    c_int16,
    c_int32,
    c_ubyte,
    c_uint16,
    c_uint32,
    c_ulong,
    c_void_p,
    create_string_buffer,
    sizeof,
)
from enum import IntEnum
from typing import TYPE_CHECKING, final

import numpy as np
from msl.loadlib import LoadLibrary

from msl.equipment.interfaces import SDK, MSLConnectionError
from msl.equipment.utils import logger

if TYPE_CHECKING:
    from ctypes import _CDataType, _CFunctionType  # pyright: ignore[reportPrivateUsage]
    from typing import Callable

    from numpy.typing import NDArray

    from msl.equipment.schema import Equipment

    from ..types import AvaSpecCallback  # noqa: TID252


IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from ctypes import WINFUNCTYPE

    func_type = WINFUNCTYPE
else:
    from ctypes import CFUNCTYPE

    func_type = CFUNCTYPE

MeasureCallback: type[_CFunctionType] = func_type(None, POINTER(c_int32), POINTER(c_int32))
"""[CFUNCTYPE][ctypes.CFUNCTYPE] function prototype to use when a measurement scan is available."""


def avaspec_callback(f: AvaSpecCallback) -> _CFunctionType:
    """Use as a decorator for a callback function when a measurement scan is available.

    See [avaspec_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/avantes/avaspec_callback.py)
    for an example usage.
    """
    return MeasureCallback(f)


WM_MEAS_READY = 0x8001
SETTINGS_RESERVED_LEN = 9720
INVALID_AVS_HANDLE_VALUE = 1000
USER_ID_LEN = 64
AVS_SERIAL_LEN = 10
MAX_TEMP_SENSORS = 3
ROOT_NAME_LEN = 6
VERSION_LEN = 16
AVASPEC_ERROR_MSG_LEN = 8
AVASPEC_MIN_MSG_LEN = 6
OEM_DATA_LEN = 4096
NR_WAVELEN_POL_COEF = 5
NR_NONLIN_POL_COEF = 8
MAX_VIDEO_CHANNELS = 2
NR_DEFECTIVE_PIXELS = 30
MAX_NR_PIXELS = 4096
NR_TEMP_POL_COEF = 5
NR_DAC_POL_COEF = 2
SAT_PEAK_INVERSION = 2
SW_TRIGGER_MODE = 0
HW_TRIGGER_MODE = 1
SS_TRIGGER_MODE = 2
EXTERNAL_TRIGGER = 0
SYNC_TRIGGER = 1
EDGE_TRIGGER_SOURCE = 0
LEVEL_TRIGGER_SOURCE = 1
ILX_FIRST_USED_DARK_PIXEL = 2
ILX_USED_DARK_PIXELS = 14
ILX_TOTAL_DARK_PIXELS = 18
TCD_FIRST_USED_DARK_PIXEL = 0
TCD_USED_DARK_PIXELS = 12
TCD_TOTAL_DARK_PIXELS = 13
HAMS9840_FIRST_USED_DARK_PIXEL = 0
HAMS9840_USED_DARK_PIXELS = 8
HAMS9840_TOTAL_DARK_PIXELS = 8
HAMS10420_FIRST_USED_DARK_PIXEL = 0
HAMS10420_USED_DARK_PIXELS = 4
HAMS10420_TOTAL_DARK_PIXELS = 4
HAMS11071_FIRST_USED_DARK_PIXEL = 0
HAMS11071_USED_DARK_PIXELS = 4
HAMS11071_TOTAL_DARK_PIXELS = 4
HAMS7031_FIRST_USED_DARK_PIXEL = 0
HAMS7031_USED_DARK_PIXELS = 4
HAMS7031_TOTAL_DARK_PIXELS = 4
HAMS11155_TOTAL_DARK_PIXELS = 20
MIN_ILX_INTTIME = 1.1
MILLI_TO_MICRO = 1000
NR_DIGITAL_OUTPUTS = 13
NR_DIGITAL_INPUTS = 13
NTC1_ID = 0
NTC2_ID = 1
TEC_ID = 2
NR_ANALOG_OUTPUTS = 2
ETH_CONN_STATUS_CONNECTING = 0
ETH_CONN_STATUS_CONNECTED = 1
ETH_CONN_STATUS_CONNECTED_NOMON = 2
ETH_CONN_STATUS_NOCONNECTION = 3


ERROR_CODES = {
    -1: ("ERR_INVALID_PARAMETER", "Function called with invalid parameter value."),
    -2: ("ERR_OPERATION_NOT_SUPPORTED", "Function not supported (e.g. use 16bit ADC mode with 14bit ADC hardware)"),
    -3: ("ERR_DEVICE_NOT_FOUND", "Opening communication failed or time-out during communication occurred."),
    -4: ("ERR_INVALID_DEVICE_ID", "AvsHandle is unknown in the DLL"),
    -5: (
        "ERR_OPERATION_PENDING",
        "Function is called while result of previous call to AVS_Measure() is not received yet",
    ),
    -6: ("ERR_TIMEOUT", "No answer received from device"),
    -7: ("Reserved", ""),
    -8: ("ERR_INVALID_MEAS_DATA", "No measurement data is received at the point AVS_GetScopeData() is called"),
    -9: ("ERR_INVALID_SIZE", "Allocated buffer size too small"),
    -10: ("ERR_INVALID_PIXEL_RANGE", "Measurement preparation failed because pixel range is invalid"),
    -11: (
        "ERR_INVALID_INT_TIME",
        "Measurement preparation failed because integration time is invalid (for selected sensor)",
    ),
    -12: (
        "ERR_INVALID_COMBINATION",
        (
            "Measurement preparation failed because of an invalid combination of parameters, "
            "e.g. integration time of 600000 and Navg > 5000"
        ),
    ),
    -13: ("Reserved", ""),
    -14: ("ERR_NO_MEAS_BUFFER_AVAIL", "Measurement preparation failed because no measurement buffers available"),
    -15: ("ERR_UNKNOWN", "Unknown error reason received from spectrometer"),
    -16: ("ERR_COMMUNICATION", "Error in communication or Ethernet connection failure"),
    -17: ("ERR_NO_SPECTRA_IN_RAM", "No more spectra available in RAM, all read or measurement not started yet"),
    -18: ("ERR_INVALID_DLL_VERSION", "DLL version information could not be retrieved"),
    -19: ("ERR_NO_MEMORY", "Memory allocation error in the DLL"),
    -20: ("ERR_DLL_INITIALISATION", "Function called before AVS_Init() is called"),
    -21: (
        "ERR_INVALID_STATE",
        (
            "Function failed because AvaSpec is in wrong state, "
            "e.g. AVS_Measure() without calling AVS_PrepareMeasurement() first"
        ),
    ),
    -22: ("ERR_INVALID_REPLY", "Reply is not a recognized protocol message"),
    -23: ("Reserved", ""),
    -24: (
        "ERR_ACCESS",
        "Error occurred while opening a bus device on the host, e.g. USB device access denied due to user rights",
    ),
    -100: ("ERR_INVALID_PARAMETER_NR_PIXEL", "NrOfPixel in Device data incorrect"),
    -101: ("ERR_INVALID_PARAMETER_ADC_GAIN", "Gain Setting Out of Range"),
    -102: ("ERR_INVALID_PARAMETER_ADC_OFFSET", "OffSet Setting Out of Range"),
    -110: (
        "ERR_INVALID_MEASPARAM_AVG_SAT2",
        "Use of Saturation Detection Level 2 is not compatible with the Averaging function",
    ),
    -111: ("ERR_INVALID_MEASPARAM_AVG_RAM", "Use of Averaging is not compatible with the StoreToRam function"),
    -112: (
        "ERR_INVALID_MEASPARAM_SYNC_RAM",
        "Use of the Synchronize setting is not compatible with the StoreToRam function",
    ),
    -113: ("ERR_INVALID_MEASPARAM_LEVEL_RAM", "Use of Level Triggering is not compatible with the StoreToRam function"),
    -114: (
        "ERR_INVALID_MEASPARAM_SAT2_RAM",
        "Use of Saturation Detection Level 2 Parameter is not compatible with the StoreToRam function",
    ),
    -115: (
        "ERR_INVALID_MEASPARAM_FWVER_RAM",
        "The StoreToRam function is only supported with firmware version 0.20.0.0 or later.",
    ),
    -116: ("ERR_INVALID_MEASPARAM_DYNDARK", "Dynamic Dark Correction not supported"),
    -120: ("ERR_NOT_SUPPORTED_BY_SENSOR_TYPE", "Use of AVS_SetSensitivityMode() not supported by detector type"),
    -121: ("ERR_NOT_SUPPORTED_BY_FW_VER", "Use of AVS_SetSensitivityMode() not supported by firmware version"),
    -122: ("ERR_NOT_SUPPORTED_BY_FPGA_VER", "Use of AVS_SetSensitivityMode() not supported by FPGA version"),
    -140: ("ERR_SL_CALIBRATION_NOT_AVAILABLE", "Spectrometer was not calibrated for stray light correction"),
    -141: ("ERR_SL_STARTPIXEL_NOT_IN_RANGE", "Incorrect start pixel found in EEPROM"),
    -142: ("ERR_SL_ENDPIXEL_NOT_IN_RANGE", "Incorrect end pixel found in EEPROM"),
    -143: ("ERR_SL_STARTPIX_GT_ENDPIX", "Incorrect start or end pixel found in EEPROM"),
    -144: ("ERR_SL_MFACTOR_OUT_OF_RANGE", "Factor should be in range 0.0 - 4.0"),
}


class DeviceStatus(IntEnum):
    """DeviceStatus enum.

    Attributes:
        UNKNOWN (int): 0
        USB_AVAILABLE (int):  1
        USB_IN_USE_BY_APPLICATION (int): 2
        USB_IN_USE_BY_OTHER (int): 3
        ETH_AVAILABLE (int): 4
        ETH_IN_USE_BY_APPLICATION (int): 5
        ETH_IN_USE_BY_OTHER (int): 6
        ETH_ALREADY_IN_USE_USB (int): 7
    """

    UNKNOWN = 0
    USB_AVAILABLE = 1
    USB_IN_USE_BY_APPLICATION = 2
    USB_IN_USE_BY_OTHER = 3
    ETH_AVAILABLE = 4
    ETH_IN_USE_BY_APPLICATION = 5
    ETH_IN_USE_BY_OTHER = 6
    ETH_ALREADY_IN_USE_USB = 7


class InterfaceType(IntEnum):
    """InterfaceType enum.

    Attributes:
        RS232 (int): 0
        USB5216 (int): 1
        USBMINI (int): 2
        USB7010 (int): 3
        ETH7010 (int): 4
    """

    RS232 = 0
    USB5216 = 1
    USBMINI = 2
    USB7010 = 3
    ETH7010 = 4


class SensType(IntEnum):
    """SensType enum.

    Attributes:
        SENS_HAMS8378_256 (int): 1
        SENS_HAMS8378_1024 (int): 2
        SENS_ILX554 (int): 3
        SENS_HAMS9201 (int): 4
        SENS_TCD1304 (int): 5
        SENS_TSL1301 (int): 6
        SENS_TSL1401 (int): 7
        SENS_HAMS8378_512 (int): 8
        SENS_HAMS9840 (int): 9
        SENS_ILX511 (int): 10
        SENS_HAMS10420_2048X64 (int): 11
        SENS_HAMS11071_2048X64 (int): 12
        SENS_HAMS7031_1024X122 (int): 13
        SENS_HAMS7031_1024X58 (int): 14
        SENS_HAMS11071_2048X16 (int): 15
        SENS_HAMS11155_2048 (int): 16
        SENS_SU256LSB (int): 17
        SENS_SU512LDB (int): 18
        SENS_HAMS11638 (int): 21
        SENS_HAMS11639 (int): 22
        SENS_HAMS12443 (int): 23
        SENS_HAMG9208_512 (int): 24
        SENS_HAMG13913 (int): 25
        SENS_HAMS13496 (int): 26
    """

    SENS_HAMS8378_256 = 1
    SENS_HAMS8378_1024 = 2
    SENS_ILX554 = 3
    SENS_HAMS9201 = 4
    SENS_TCD1304 = 5
    SENS_TSL1301 = 6
    SENS_TSL1401 = 7
    SENS_HAMS8378_512 = 8
    SENS_HAMS9840 = 9
    SENS_ILX511 = 10
    SENS_HAMS10420_2048X64 = 11
    SENS_HAMS11071_2048X64 = 12
    SENS_HAMS7031_1024X122 = 13
    SENS_HAMS7031_1024X58 = 14
    SENS_HAMS11071_2048X16 = 15
    SENS_HAMS11155_2048 = 16
    SENS_SU256LSB = 17
    SENS_SU512LDB = 18
    SENS_HAMS11638 = 21
    SENS_HAMS11639 = 22
    SENS_HAMS12443 = 23
    SENS_HAMG9208_512 = 24
    SENS_HAMG13913 = 25
    SENS_HAMS13496 = 26


@final
class AvsIdentityType(Structure):
    """IdentityType Structure.

    Attributes:
        SerialNumber (c_char * 10): Serial number of device.
        UserFriendlyName (c_char * 64): User-friendly name.
        Status (c_ubyte): Device status.
    """

    _pack_ = 1
    _fields_ = (
        ("SerialNumber", c_char * AVS_SERIAL_LEN),
        ("UserFriendlyName", c_char * USER_ID_LEN),
        ("Status", c_ubyte),
    )


@final
class BroadcastAnswerType(Structure):
    """BroadcastAnswerType Structure.

    Attributes:
        InterfaceType (c_ubyte): InterfaceType
        serial (c_ubyte * 10): serial
        port (c_uint16): port
        status (c_ubyte): status
        RemoteHostIp (c_uint32): RemoteHostIp
        LocalIp (c_uint32): LocalIp
        reserved (c_ubyte * 4): reserved
    """

    _pack_ = 1
    _fields_ = (
        ("InterfaceType", c_ubyte),
        ("serial", c_ubyte * AVS_SERIAL_LEN),
        ("port", c_uint16),
        ("status", c_ubyte),
        ("RemoteHostIp", c_uint32),
        ("LocalIp", c_uint32),
        ("reserved", c_ubyte * 4),
    )


@final
class ControlSettingsType(Structure):
    """ControlSettingsType Structure.

    Attributes:
        m_StrobeControl (c_uint16): m_StrobeControl
        m_LaserDelay (c_uint32): m_LaserDelay
        m_LaserWidth (c_uint32): m_LaserWidth
        m_LaserWaveLength (c_float): m_LaserWaveLength
        m_StoreToRam (c_uint16): m_StoreToRam
    """

    _pack_ = 1
    _fields_ = (
        ("m_StrobeControl", c_uint16),
        ("m_LaserDelay", c_uint32),
        ("m_LaserWidth", c_uint32),
        ("m_LaserWaveLength", c_float),
        ("m_StoreToRam", c_uint16),
    )


@final
class DarkCorrectionType(Structure):
    """DarkCorrectionType Structure.

    Attributes:
        m_Enable (c_ubyte): m_Enable
        m_ForgetPercentage (c_ubyte): m_ForgetPercentage
    """

    _pack_ = 1
    _fields_ = (
        ("m_Enable", c_ubyte),
        ("m_ForgetPercentage", c_ubyte),
    )


@final
class DetectorType(Structure):
    """DetectorType Structure.

    Attributes:
        m_SensorType (c_ubyte): m_SensorType
        m_NrPixels (c_uint16): m_NrPixels
        m_aFit (c_float * 5): m_aFit
        m_NLEnable (c_bool): m_NLEnable
        m_aNLCorrect (c_double * 8): m_aNLCorrect
        m_aLowNLCounts (c_double): m_aLowNLCounts
        m_aHighNLCounts (c_double): m_aHighNLCounts
        m_Gain (c_float * 2): m_Gain
        m_Reserved (c_float): m_Reserved
        m_Offset (c_float * 2): m_Offset
        m_ExtOffset (c_float): m_ExtOffset
        m_DefectivePixels (c_uint16 * 30): m_DefectivePixels
    """

    _pack_ = 1
    _fields_ = (
        ("m_SensorType", c_ubyte),
        ("m_NrPixels", c_uint16),
        ("m_aFit", c_float * NR_WAVELEN_POL_COEF),
        ("m_NLEnable", c_bool),
        ("m_aNLCorrect", c_double * NR_NONLIN_POL_COEF),
        ("m_aLowNLCounts", c_double),
        ("m_aHighNLCounts", c_double),
        ("m_Gain", c_float * MAX_VIDEO_CHANNELS),
        ("m_Reserved", c_float),
        ("m_Offset", c_float * MAX_VIDEO_CHANNELS),
        ("m_ExtOffset", c_float),
        ("m_DefectivePixels", c_uint16 * NR_DEFECTIVE_PIXELS),
    )


@final
class SmoothingType(Structure):
    """SmoothingType Structure.

    Attributes:
        m_SmoothPix (c_uint16): m_SmoothPix
        m_SmoothModel (c_ubyte): m_SmoothModel
    """

    _pack_ = 1
    _fields_ = (
        ("m_SmoothPix", c_uint16),
        ("m_SmoothModel", c_ubyte),
    )


@final
class SpectrumCalibrationType(Structure):
    """SpectrumCalibrationType Structure.

    Attributes:
        m_Smoothing (SmoothingType): m_Smoothing
        m_CalInttime (c_float): m_CalInttime
        m_aCalibConvers (c_float * 4096): m_aCalibConvers
    """

    _pack_ = 1
    _fields_ = (
        ("m_Smoothing", SmoothingType),
        ("m_CalInttime", c_float),
        ("m_aCalibConvers", c_float * MAX_NR_PIXELS),
    )


@final
class IrradianceType(Structure):
    """IrradianceType Structure.

    Attributes:
        m_IntensityCalib (SpectrumCalibrationType): m_IntensityCalib
        m_CalibrationType (c_ubyte): m_CalibrationType
        m_FiberDiameter (c_uint32): m_FiberDiameter
    """

    _pack_ = 1
    _fields_ = (
        ("m_IntensityCalib", SpectrumCalibrationType),
        ("m_CalibrationType", c_ubyte),
        ("m_FiberDiameter", c_uint32),
    )


@final
class SpectrumCorrectionType(Structure):
    """SpectrumCorrectionType Structure.

    Attributes:
        m_aSpectrumCorrect (c_float * 4096): m_aSpectrumCorrect
    """

    _pack_ = 1
    _fields_ = (("m_aSpectrumCorrect", c_float * MAX_NR_PIXELS),)


@final
class TriggerType(Structure):
    """TriggerType Structure.

    Attributes:
        m_Mode (c_ubyte): m_Mode
        m_Source (c_ubyte): m_Source
        m_SourceType (c_ubyte): m_SourceType
    """

    _pack_ = 1
    _fields_ = (
        ("m_Mode", c_ubyte),
        ("m_Source", c_ubyte),
        ("m_SourceType", c_ubyte),
    )


@final
class MeasConfigType(Structure):
    """MeasConfigType Structure.

    Attributes:
        m_StartPixel (c_uint16): m_StartPixel
        m_StopPixel (c_uint16): m_StopPixel
        m_IntegrationTime (c_float): m_IntegrationTime
        m_IntegrationDelay (c_uint32): m_IntegrationDelay
        m_NrAverages (c_uint32): m_NrAverages
        m_CorDynDark (DarkCorrectionType): m_CorDynDark
        m_Smoothing (SmoothingType): m_Smoothing
        m_SaturationDetection (c_ubyte): m_SaturationDetection
        m_Trigger (TriggerType): m_Trigger
        m_Control (ControlSettingsType): m_Control
    """

    _pack_ = 1
    _fields_ = (
        ("m_StartPixel", c_uint16),
        ("m_StopPixel", c_uint16),
        ("m_IntegrationTime", c_float),
        ("m_IntegrationDelay", c_uint32),
        ("m_NrAverages", c_uint32),
        ("m_CorDynDark", DarkCorrectionType),
        ("m_Smoothing", SmoothingType),
        ("m_SaturationDetection", c_ubyte),
        ("m_Trigger", TriggerType),
        ("m_Control", ControlSettingsType),
    )


@final
class TimeStampType(Structure):
    """TimeStampType Structure.

    Attributes:
        m_Date (c_uint16): m_Date
        m_Time (c_uint16): m_Time
    """

    _pack_ = 1
    _fields_ = (
        ("m_Date", c_uint16),
        ("m_Time", c_uint16),
    )


@final
class StandAloneType(Structure):
    """StandAloneType Structure.

    Attributes:
        m_Enable (c_bool): m_Enable
        m_Meas (MeasConfigType): m_Meas
        m_Nmsr (c_int16): m_Nmsr
    """

    _pack_ = 1
    _fields_ = (("m_Enable", c_bool), ("m_Meas", MeasConfigType), ("m_Nmsr", c_int16))


@final
class DynamicStorageType(Structure):
    """DynamicStorageType Structure.

    Attributes:
        m_Nmsr (c_int32): m_Nmsr
        m_Reserved (c_ubyte * 8): m_Reserved
    """

    _pack_ = 1
    _fields_ = (
        ("m_Nmsr", c_int32),
        ("m_Reserved", c_ubyte * 8),
    )


@final
class TempSensorType(Structure):
    """TempSensorType Structure.

    Attributes:
        m_aFit (c_float * 5): m_aFit
    """

    _pack_ = 1
    _fields_ = (("m_aFit", c_float * NR_TEMP_POL_COEF),)


@final
class TecControlType(Structure):
    """TecControlType Structure.

    Attributes:
        m_Enable (c_bool): m_Enable
        m_Setpoint (c_float): m_Setpoint
        m_aFit (c_float * 2): m_aFit
    """

    _pack_ = 1
    _fields_ = (
        ("m_Enable", c_bool),
        ("m_Setpoint", c_float),
        ("m_aFit", c_float * NR_DAC_POL_COEF),
    )


@final
class ProcessControlType(Structure):
    """ProcessControlType Structure.

    Attributes:
        m_AnalogLow (c_float * 2): m_AnalogLow
        m_AnalogHigh (c_float * 2): m_AnalogHigh
        m_DigitalLow (c_float * 10): m_DigitalLow
        m_DigitalHigh (c_float * 10): m_DigitalHigh
    """

    _pack_ = 1
    _fields_ = (
        ("m_AnalogLow", c_float * 2),
        ("m_AnalogHigh", c_float * 2),
        ("m_DigitalLow", c_float * 10),
        ("m_DigitalHigh", c_float * 10),
    )


@final
class EthernetSettingsType(Structure):
    """EthernetSettingsType Structure.

    Attributes:
        m_IpAddr(c_uint32): m_IpAddr
        m_NetMask (c_uint32): m_NetMask
        m_Gateway (c_uint32): m_Gateway
        m_DhcpEnabled (c_ubyte): m_DhcpEnabled
        m_TcpPort (c_uint16): m_TcpPort
        m_LinkStatus (c_ubyte): m_LinkStatus
    """

    _pack_ = 1
    _fields_ = (
        ("m_IpAddr", c_uint32),
        ("m_NetMask", c_uint32),
        ("m_Gateway", c_uint32),
        ("m_DhcpEnabled", c_ubyte),
        ("m_TcpPort", c_uint16),
        ("m_LinkStatus", c_ubyte),
    )


@final
class OemDataType(Structure):
    """OemDataType Structure.

    Attributes:
        m_data (c_ubyte * 4096): m_data
    """

    _pack_ = 1
    _fields_ = (("m_data", c_ubyte * OEM_DATA_LEN),)


@final
class HeartbeatRespType(Structure):
    """HeartbeatRespType Structure.

    Attributes:
        m_BitMatrix (c_uint32): m_BitMatrix
        m_Reserved (c_uint32): m_Reserved
    """

    _pack_ = 1
    _fields_ = (("m_BitMatrix", c_uint32), ("m_Reserved", c_uint32))


@final
class DeviceConfigType(Structure):
    """DeviceConfigType Structure.

    Attributes:
        m_Len (c_uint16): m_Len
        m_ConfigVersion (c_uint16): m_ConfigVersion
        m_aUserFriendlyId (c_char * 64): m_aUserFriendlyId
        m_Detector (DetectorType): m_Detector
        m_Irradiance (IrradianceType): m_Irradiance
        m_Reflectance (SpectrumCalibrationType): m_Reflectance
        m_SpectrumCorrect (SpectrumCorrectionType): m_SpectrumCorrect
        m_StandAlone (StandAloneType): m_StandAlone
        m_DynamicStorage (DynamicStorageType): m_DynamicStorage
        m_aTemperature (TempSensorType * 3): m_aTemperature
        m_TecControl (TecControlType): m_TecControl
        m_ProcessControl (ProcessControlType): m_ProcessControl
        m_EthernetSettings (EthernetSettingsType): m_EthernetSettings
        m_aReserved (c_ubyte * 9720): m_aReserved
        m_OemData (OemDataType): m_OemData
    """

    _pack_ = 1
    _fields_ = (
        ("m_Len", c_uint16),
        ("m_ConfigVersion", c_uint16),
        ("m_aUserFriendlyId", c_char * USER_ID_LEN),
        ("m_Detector", DetectorType),
        ("m_Irradiance", IrradianceType),
        ("m_Reflectance", SpectrumCalibrationType),
        ("m_SpectrumCorrect", SpectrumCorrectionType),
        ("m_StandAlone", StandAloneType),
        ("m_DynamicStorage", DynamicStorageType),
        ("m_aTemperature", TempSensorType * MAX_TEMP_SENSORS),
        ("m_TecControl", TecControlType),
        ("m_ProcessControl", ProcessControlType),
        ("m_EthernetSettings", EthernetSettingsType),
        ("m_aReserved", c_ubyte * SETTINGS_RESERVED_LEN),
        ("m_OemData", OemDataType),
    )


_handles: list[int] = []


@final
class AvaSpec(SDK, manufacturer=r"Avantes", model=r"."):
    """Wrapper around the `avaspec` SDK from [Avantes](https://www.avantes.com/){:target="_blank"}."""

    def __init__(self, equipment: Equipment) -> None:
        """Wrapper around the `avaspec` SDK from Avantes.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Avantes"
        model=r"."
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the AvaSpec wrapper.

        Attributes: Connection Properties:
            port_id (int): One of `-1` (Ethernet+USB), `0` (USB) or `256` (Ethernet). _Default: `-1`_
            activate (bool): Whether to automatically activate the connection. _Default: `True`_
        """
        self._handle: int | None = None
        super().__init__(equipment, libtype="windll" if IS_WINDOWS else "cdll")

        functions: dict[
            str, tuple[type[c_int32 | c_bool], Callable[..., int | None], list[tuple[str, type[_CDataType]]]]
        ] = {
            "AVS_Init": (c_int32, self._err_check, [("a_Port", c_int16)]),
            "AVS_Done": (c_int32, self._err_check, []),
            "AVS_GetNrOfDevices": (c_int32, self._log_errcheck, []),
            "AVS_UpdateUSBDevices": (c_int32, self._log_errcheck, []),
            "AVS_UpdateETHDevices": (
                c_int32,
                self._err_check,
                [
                    ("a_ListSize", c_uint32),
                    ("a_pRequiredSize", POINTER(c_uint32)),
                    ("a_pList", POINTER(BroadcastAnswerType)),
                ],
            ),
            "AVS_GetList": (
                c_int32,
                self._err_check,
                [
                    ("a_ListSize", c_uint32),
                    ("a_pRequiredSize", POINTER(c_uint32)),
                    ("a_pList", POINTER(AvsIdentityType)),
                ],
            ),
            "AVS_Activate": (c_int32, self._err_check, [("a_pDeviceId", POINTER(AvsIdentityType))]),
            "AVS_ActivateConn": (c_int32, self._err_check, [("a_pDeviceId", POINTER(AvsIdentityType))]),
            "AVS_ActivateConnCb": (c_int32, self._err_check, [("a_pDeviceId", POINTER(AvsIdentityType))]),
            "AVS_Deactivate": (c_bool, self._check_bool, [("a_hDevice", c_int32)]),
            "AVS_GetHandleFromSerial": (c_int32, self._err_check, [("a_pSerial", c_char_p)]),
            "AVS_GetStatusBySerial": (
                c_int32,
                self._err_check,
                [("a_pSerial", c_char_p), ("a_status", POINTER(c_int32))],
            ),
            "AVS_Register": (c_bool, self._check_bool, [("a_Hwnd", c_void_p)]),
            "AVS_Measure": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_hWnd", c_void_p), ("a_Nmsr", c_int16)],
            ),
            "AVS_MeasureCallback": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("__Done", MeasureCallback), ("a_Nmsr", c_int16)],
            ),
            "AVS_PrepareMeasure": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pMeasConfig", POINTER(MeasConfigType))],
            ),
            "AVS_StopMeasure": (c_int32, self._err_check, [("a_hDevice", c_int32)]),
            "AVS_PollScan": (c_int32, self._err_check, [("a_hDevice", c_int32)]),
            "AVS_GetScopeData": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pTimeLabel", POINTER(c_uint32)), ("a_pSpectrum", POINTER(c_double))],
            ),
            "AVS_GetSaturatedPixels": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pSaturated", POINTER(c_ubyte))],
            ),
            "AVS_GetLambda": (c_int32, self._err_check, [("a_hDevice", c_int32), ("a_pWaveLength", POINTER(c_double))]),
            "AVS_GetNumPixels": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pNumPixels", POINTER(c_uint16))],
            ),
            "AVS_GetParameter": (
                c_int32,
                self._err_check,
                [
                    ("a_hDevice", c_int32),
                    ("a_Size", c_uint32),
                    ("a_pRequiredSize", POINTER(c_uint32)),
                    ("a_pDeviceParm", POINTER(DeviceConfigType)),
                ],
            ),
            "AVS_SetParameter": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pDeviceParm", POINTER(DeviceConfigType))],
            ),
            "AVS_GetVersionInfo": (
                c_int32,
                self._err_check,
                [
                    ("a_hDevice", c_int32),
                    ("a_pFPGAVersion", c_char_p),
                    ("a_pFirmwareVersion", c_char_p),
                    ("a_pDLLVersion", c_char_p),
                ],
            ),
            "AVS_GetDLLVersion": (c_int32, self._err_check, [("a_pVersionString", c_char_p)]),
            "AVS_SetSyncMode": (c_int32, self._err_check, [("a_hDevice", c_int32), ("a_Enable", c_ubyte)]),
            "AVS_SetPrescanMode": (c_int32, self._err_check, [("a_hDevice", c_int32), ("a_Prescan", c_bool)]),
            "AVS_UseHighResAdc": (c_int32, self._err_check, [("a_hDevice", c_int32), ("a_Enable", c_bool)]),
            "AVS_GetAnalogIn": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_AnalogInId", c_ubyte), ("a_pAnalogIn", POINTER(c_float))],
            ),
            "AVS_GetDigIn": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_DigInId", c_ubyte), ("a_pDigIn", POINTER(c_ubyte))],
            ),
            "AVS_SetAnalogOut": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_PortId", c_ubyte), ("a_Value", c_float)],
            ),
            "AVS_SetDigOut": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_PortId", c_ubyte), ("a_Status", c_ubyte)],
            ),
            "AVS_SetPwmOut": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_PortId", c_ubyte), ("a_Freq", c_ulong), ("a_Duty", c_ubyte)],
            ),
            "AVS_GetDarkPixelData": (
                c_int32,
                self._check_bool,
                [("a_hDevice", c_int32), ("a_pDarkData", POINTER(c_double))],
            ),
            "AVS_GetComPortName": (
                c_int32,
                self._check_bool,
                [("a_pDeviceId", POINTER(AvsIdentityType)), ("a_pIp", c_char_p), ("a_size", POINTER(c_int32))],
            ),
            "AVS_GetComType": (
                c_int32,
                self._err_check,
                [("a_pDeviceId", POINTER(AvsIdentityType)), ("a_type", POINTER(c_int32))],
            ),
            "AVS_SetSensitivityMode": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_SensitivityMode", c_uint32)],
            ),
            "AVS_GetIpConfig": (
                c_int32,
                self._check_bool,
                [("a_hDevice", c_int32), ("a_Data", POINTER(EthernetSettingsType))],
            ),
            "AVS_SuppressStrayLight": (
                c_int32,
                self._err_check,
                [
                    ("a_hDevice", c_int32),
                    ("a_Multifactor", c_float),
                    ("a_pSrcSpectrum", POINTER(c_double)),
                    ("a_pDestSpectrum", POINTER(c_double)),
                ],
            ),
            "AVS_Heartbeat": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pHbReq", POINTER(c_uint32)), ("a_pHbResp", POINTER(HeartbeatRespType))],
            ),
            "AVS_ResetDevice": (c_int32, self._err_check, [("a_hDevice", c_int32)]),
            "AVS_GetOemParameter": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pOemData", POINTER(OemDataType))],
            ),
            "AVS_SetOemParameter": (
                c_int32,
                self._err_check,
                [("a_hDevice", c_int32), ("a_pOemData", POINTER(OemDataType))],
            ),
        }

        for key, value in functions.items():
            try:
                attr = getattr(self.sdk, key)
            except AttributeError as e:  # noqa: PERF203
                logger.debug("%s: %s", self.__class__.__name__, e)
            else:
                attr.restype, attr.errcheck = value[:2]
                attr.argtypes = [typ for _, typ in value[2]]

        assert equipment.connection  # noqa: S101
        props = equipment.connection.properties
        _ = self.init(props.get("port_id", -1))
        if props.get("activate", True):
            self.activate()

    def _check_bool(self, result: bool, func: object, arguments: tuple[object, ...]) -> None:  # noqa: FBT001
        self._log_errcheck(result, func, arguments)
        if not result:
            raise MSLConnectionError(self, f"The {func} function returned False")

    def _err_check(self, result: int, func: object, arguments: tuple[object, ...]) -> int:
        self._log_errcheck(result, func, arguments)
        if result < 0:
            error_name, msg = ERROR_CODES.get(result, ("UNKNOWN_ERROR", f"Unknown error [code={result}]"))
            raise MSLConnectionError(self, f"{error_name}: {msg}")
        return result

    def activate(self) -> None:
        """Activates the spectrometer for communication."""
        out = AvaSpec.find(path=self.path)
        if not out:
            raise MSLConnectionError(self, "Cannot activate. No devices found.")

        for item in out:
            if item.SerialNumber.decode() == self.equipment.serial:
                self._handle = int(self.sdk.AVS_Activate(item))
                if self._handle == INVALID_AVS_HANDLE_VALUE:
                    raise MSLConnectionError(self, "Invalid handle")
                _handles.append(self._handle)
                return

        msg = f"Did not find the Avantes serial number {self.equipment.serial!r} in the list of devices."
        raise MSLConnectionError(self, msg)

    def deactivate(self) -> None:
        """Closes communication with the spectrometer."""
        if self._handle in _handles:
            self.sdk.AVS_Deactivate(self._handle)
            _handles.remove(self._handle)
            self._handle = None
            super().disconnect()

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Calls [deactivate][msl.equipment_resources.avantes.avaspec.AvaSpec.deactivate].

        Also calls [done][msl.equipment_resources.avantes.avaspec.AvaSpec.done] (if there
        are no additional connections open to other spectrometers).
        """
        self.deactivate()
        if not _handles:
            self.done()

    def done(self) -> None:
        """Closes communication with all spectrometers and releases internal storage."""
        if hasattr(self, "_sdk") and self._sdk is not None:
            self.sdk.AVS_Done()

    @staticmethod
    def find(path: str = "avaspecx64", port_id: int = -1, nmax: int = 16) -> list[AvsIdentityType]:
        """Returns device information for each spectrometer that is connected.

        Args:
            path: The path to the AvaSpec SDK.
            port_id: ID of port to be used. One of:

                * `-1`: Use both Ethernet (AS7010) and USB ports
                * `0`: Use USB port
                * `1..255`: Not supported in v9.7 of the SDK
                * `256`: Use Ethernet port (AS7010)

            nmax: The maximum number of devices that can be in the list.

        Returns:
            The information about the devices.
        """
        lib = LoadLibrary(path, libtype="windll" if IS_WINDOWS else "cdll").lib

        ret = lib.AVS_Init(port_id)
        if ret == 0:
            return []

        size = nmax * sizeof(AvsIdentityType)
        required_size = c_uint32()
        types = (AvsIdentityType * nmax)()

        lib.AVS_GetList.argtypes = [c_uint32, POINTER(c_uint32), POINTER(AvsIdentityType)]
        n = lib.AVS_GetList(size, required_size, types)
        if n >= 0:
            return [types[i] for i in range(n)]

        error_name, msg = ERROR_CODES.get(n, ("UNKNOWN_ERROR", f"Unknown error [code={n}]"))
        msg = f"{error_name}: {msg}"
        raise RuntimeError(msg)

    def get_analog_in(self, analog_id: int) -> float:
        """Get the status of the specified analog input.

        Args:
            analog_id: The identifier of the analog input to get.

                * AS5216:

                    * 0 = thermistor on optical bench (NIR 2.0 / NIR2.2 / NIR 2.5 / TEC)
                    * 1 = 1V2
                    * 2 = 5VIO
                    * 3 = 5VUSB
                    * 4 = AI2 = pin 18 at 26-pin connector
                    * 5 = AI1 = pin 9 at 26-pin connector
                    * 6 = NTC1 onboard thermistor
                    * 7 = Not used

                * Mini:

                    * 0 = NTC1 onboard thermistor
                    * 1 = Not used
                    * 2 = Not used
                    * 3 = Not used
                    * 4 = AI2 = pin 13 on micro HDMI = pin 11 on HDMI Terminal
                    * 5 = AI1 = pin 16 on micro HDMI = pin 17 on HDMI Terminal
                    * 6 = Not used
                    * 7 = Not used

                * AS7010:

                    * 0 = thermistor on optical bench (NIR 2.0 / NIR2.2 / NIR 2.5 / TEC)
                    * 1 = Not used
                    * 2 = Not used
                    * 3 = Not used
                    * 4 = AI2 = pin 18 at 26-pin connector
                    * 5 = AI1 = pin 9 at 26-pin connector
                    * 6 = digital temperature sensor, returns degrees Celsius, not Volts
                    * 7 = Not used

        Returns:
            The analog input value [Volts or degrees Celsius].
        """
        ain = c_float()
        self.sdk.AVS_GetAnalogIn(self._handle, analog_id, ain)
        return ain.value

    def get_com_port_name(self) -> str:
        """Get the IP address of the device.

        Returns:
            The IP address of the device.
        """
        device_id = AvsIdentityType()
        device_id.SerialNumber = self.equipment.serial.encode()
        name = create_string_buffer(255)
        self.sdk.AVS_GetComPortName(device_id, name, len(name))
        return name.value.decode()

    def get_com_type(self) -> int:
        """Get the communication protocol.

        Returns:
            The communication type as defined below:
                * 0 = RS232
                * 1 = USB5216
                * 2 = USBMINI
                * 3 = USB7010
                * 4 = ETH7010
                * -1 = UNKNOWN
        """
        device_id = AvsIdentityType()
        device_id.SerialNumber = self.equipment.serial.encode()
        typ = c_int32(-1)
        self.sdk.AVS_GetComType(device_id, typ)
        return typ.value

    def get_dark_pixel_data(self) -> NDArray[np.double]:
        """Get the optically black pixel values of the last performed measurement.

        You must call [get_data][msl.equipment_resources.avantes.avaspec.AvaSpec.get_data] before you call this method.

        Returns:
            The dark pixels.
        """
        # from the docs the maximum size is size=18 for the AvaSpec-2048-USB2 and AvaSpec-2048L-USB2
        values = np.zeros(32, dtype=np.double)  # make it bigger than 18
        self.sdk.AVS_GetDarkPixelData(self._handle, values.ctypes.data_as(POINTER(c_double)))
        return values[values > 0]

    def get_data(self) -> tuple[int, NDArray[np.double]]:
        """Returns the timestamp and the spectral data of the last measurement.

        Returns:
            The timestamp and the spectral data.
        """
        ticks = c_uint32()
        values = np.ones(MAX_NR_PIXELS, dtype=np.double) * -1.0
        self.sdk.AVS_GetScopeData(self._handle, ticks, values.ctypes.data_as(POINTER(c_double)))
        return ticks.value, values[values > -1.0]

    def get_digital_in(self, digital_id: int) -> int:
        """Get the status of the specified digital input.

        Args:
            digital_id: The identifier of the digital input to get.

                * AS5216:

                    * `0`: DI1 = Pin 24 at 26-pin connector
                    * `1`: DI2 = Pin 7 at 26-pin connector
                    * `2`: DI3 = Pin 16 at 26-pin connector

                * Mini:

                    * `0`: DI1 = Pin 7 on Micro HDMI = Pin 5 on HDMI terminal
                    * `1`: DI2 = Pin 5 on Micro HDMI = Pin 3 on HDMI Terminal
                    * `2`: DI3 = Pin 3 on Micro HDMI = Pin 1 on HDMI Terminal
                    * `3`: DI4 = Pin 1 on Micro HDMI = Pin 19 on HDMI Terminal
                    * `4`: DI5 = Pin 4 on Micro HDMI = Pin 2 on HDMI Terminal
                    * `5`: DI6 = Pin 2 on Micro HDMI = Pin 14 on HDMI Terminal

                * AS7010:

                    * `0`: DI1 = Pin 24 at 26-pin connector
                    * `1`: DI2 = Pin 7 at 26-pin connector
                    * `2`: DI3 = Pin 16 at 26-pin

        Returns:
            The digital input value.
        """
        din = c_ubyte()
        self.sdk.AVS_GetDigIn(self._handle, digital_id, din)
        return din.value

    def get_dll_version(self) -> str:
        """Get the DLL version number.

        Returns:
            The DLL version number
        """
        version = create_string_buffer(255)
        self.sdk.AVS_GetDLLVersion(version)
        return version.value.decode()

    def get_handle_from_serial(self, serial: str | None = None) -> int:
        """Get the handle ID for the specified serial number.

        Args:
            serial: The serial number. Default is to get the handle for this class instance.

        Returns:
            The handle.
        """
        serial = serial or self.equipment.serial
        return int(self.sdk.AVS_GetHandleFromSerial(serial.encode()))

    def get_ip_config(self) -> EthernetSettingsType:
        """Retrieve IP settings from the spectrometer.

        Use this function to read the Ethernet settings of the spectrometer, without
        having to read the complete device configuration structure.

        Returns:
            The Ethernet settings of the spectrometer.
        """
        eth = EthernetSettingsType()
        self.sdk.AVS_GetIpConfig(self._handle, eth)
        return eth

    def get_lambda(self) -> NDArray[np.double]:
        """Returns the wavelength values corresponding to the pixels if available.

        Returns:
            The wavelength value of each pixel.
        """
        values = np.zeros(MAX_NR_PIXELS, dtype=np.double)
        self.sdk.AVS_GetLambda(self._handle, values.ctypes.data_as(POINTER(c_double)))
        return values[values > 0]

    def get_num_devices(self) -> int:
        """Scans for attached devices and returns the number of devices detected.

        Deprecated function, replaced by :meth:`.update_usb_devices`. The
        functionality is identical.

        Returns:
            The number of devices found.
        """
        num: int = self.sdk.AVS_GetNrOfDevices()
        return num

    def get_num_pixels(self) -> int:
        """Returns the number of pixels of a spectrometer."""
        n = c_uint16()
        self.sdk.AVS_GetNumPixels(self._handle, n)
        return n.value

    def get_oem_parameter(self) -> OemDataType:
        """Returns the OEM data structure available on the spectrometer.

        Returns:
            The OEM parameters.
        """
        odt = OemDataType()
        self.sdk.AVS_GetOemParameter(self._handle, odt)
        return odt

    def get_parameter(self) -> DeviceConfigType:
        """Returns the device information of the spectrometer.

        Returns:
            The device parameters.
        """
        dct = DeviceConfigType()
        required_size = c_uint32()
        self.sdk.AVS_GetParameter(self._handle, sizeof(dct), required_size, dct)
        return dct

    def get_saturated_pixels(self) -> NDArray[np.uint8]:
        """Returns, for each pixel, if a pixel was saturated (1) or not (0).

        Returns:
            The saturation state of each pixel.
        """
        n = 9
        values = np.full(MAX_NR_PIXELS, n, dtype=np.uint8)
        self.sdk.AVS_GetSaturatedPixels(self._handle, values.ctypes.data_as(POINTER(c_ubyte)))
        return values[values < n]

    def get_status_by_serial(self, serial: str | None = None) -> int:
        """Get the handle ID for the specified serial number.

        Args:
            serial: The serial number. Default is to get the status for this class instance.

        Returns:
            The status.
        """
        serial = serial or self.equipment.serial
        status = c_int32()
        self.sdk.AVS_GetStatusBySerial(serial.encode(), status)
        return status.value

    def get_version_info(self) -> tuple[str, str, str]:
        """Returns software version information.

        Returns:
            FPGA software version, firmware version, DLL version.
        """
        fpga = create_string_buffer(16)
        fm = create_string_buffer(16)
        dll = create_string_buffer(16)
        self.sdk.AVS_GetVersionInfo(self._handle, fpga, fm, dll)
        return fpga.value.decode(), fm.value.decode(), dll.value.decode()

    def heartbeat(self, req_type: int) -> HeartbeatRespType:
        """Monitor the (heartbeat) functions of the spectrometer.

        This function applies only to the AS7010 platform. See the DLL manual for more details.

        Args:
            req_type: The heartbeat request values used to control heartbeat functions.

        Returns:
            The heartbeat response structure received from the spectrometer.
        """
        resp = HeartbeatRespType()
        self.sdk.AVS_Heartbeat(self._handle, req_type, resp)
        return resp

    def init(self, port_id: int) -> int:
        """Initializes the communication interface with the spectrometers and the internal data structures.

        For Ethernet devices this function will create a list of available Ethernet spectrometers
        within all the network interfaces of the host.

        Args:
            port_id: ID of port to be used. One of:

                * `-1`: Use both Ethernet (AS7010) and USB ports
                * `0`: Use USB port
                * `1..255`: Not supported in v9.7 of the SDK
                * `256`: Use Ethernet port (AS7010)

        Returns:
            On success, the number of connected or found devices.
        """
        ret = int(self.sdk.AVS_Init(port_id))
        if ret == 0:
            raise MSLConnectionError(self, "No Avantes devices were found")
        return ret

    def measure(self, num_measurements: int, window_handle: int | None = None) -> None:
        """Starts measurement on the spectrometer.

        Args:
            num_measurements: Number of measurements to acquire. Use -1 to measure continuously until
                [stop_measure][msl.equipment_resources.avantes.avaspec.AvaSpec.stop_measure] is called.
            window_handle: Window handle to notify application measurement result data is available.
                The DLL sends a message to the window with command: `WM_MEAS_READY`, with `SUCCESS` (`0`),
                the number of scans that were saved in RAM (if `m_StoreToRAM` parameter > 0, see
                [ControlSettingsType][msl.equipment_resources.avantes.avaspec.ControlSettingsType]),
                or `INVALID_MEAS_DATA` as `WPARM` value and `a_hDevice` as `LPARM` value. Set this
                value to `None` if a callback is not needed.
        """
        self.sdk.AVS_Measure(self._handle, window_handle, num_measurements)

    def measure_callback(self, num_measurements: int, callback: AvaSpecCallback | None = None) -> None:
        """Register a measurement-available callback function for the spectrometer.

        !!! example
            See [avaspec_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/avantes/avaspec_callback.py)
            for an example usage.

        Args:
            num_measurements: Number of measurements to acquire. Use -1 to measure continuously until
                [stop_measure][msl.equipment_resources.avantes.avaspec.AvaSpec.stop_measure] is called.
            callback: A callback function to notify that application measurement result data is available.
                The DLL will call the given function to notify a measurement is ready and pass two parameters.
                The first parameter is a reference to the DLL handle. The second parameter is a reference to
                an integer value: `SUCCESS` (`0`) if a new scan is available, or the number of scans that were
                saved in RAM (if `m_StoreToRAM` parameter > 0, see
                [ControlSettingsType][msl.equipment_resources.avantes.avaspec.ControlSettingsType]),
                or `INVALID_MEAS_DATA` (`-8`). Set this value to `None` if a callback is not needed.
        """
        self.sdk.AVS_MeasureCallback(self._handle, callback, num_measurements)

    def poll_scan(self) -> bool:
        """Determines if new measurement results are available.

        Returns:
            Whether there is a scan available.
        """
        return bool(self.sdk.AVS_PollScan(self._handle))

    def prepare_measure(self, config: MeasConfigType) -> None:
        """Prepares measurement on the spectrometer using the specified measurement configuration.

        Args:
            config: The measurement configuration.
        """
        self.sdk.AVS_PrepareMeasure(self._handle, config)

    def register(self, handle: int) -> None:
        """Installs an application windows handle to which device attachment/removal messages have to be sent.

        Args:
            handle: Application window handle.
        """
        self.sdk.AVS_Register(handle)

    def reset_device(self) -> None:
        """Performs a hard reset on the given spectrometer.

        This function only works with the AS7010 platform.

        During reset of the spectrometer, all spectrometer HW modules (microprocessor and USB controller)
        will be reset at once. The spectrometer will start its reset procedure right after sending the
        command response back to the host.
        """
        self.sdk.AVS_ResetDevice(self._handle)

    def set_analog_out(self, port_id: int, value: float) -> None:
        """Sets the analog output value for the specified analog identifier.

        Args:
            port_id: Identifier for one of the two output signals:

                * AS5216:

                    * `0`: AO1 = pin 17 at 26-pin connector
                    * `1`: AO2 = pin 26 at 26-pin connector

                * Mini:

                    * `0`: AO1 = Pin 12 on Micro HDMI = Pin 10 on HDMI terminal
                    * `1`: AO2 = Pin 14 on Micro HDMI = Pin 12 on HDMI terminal

                * AS7010:

                    * `0`: AO1 = pin 17 at 26-pin connector
                    * `1`: AO2 = pin 26 at 26-pin connector

            value: DAC value to be set in Volts (internally an 8-bits DAC is used) with range 0 - 5V.
        """
        self.sdk.AVS_SetAnalogOut(self._handle, port_id, value)

    def set_digital_out(self, port_id: int, value: int) -> None:
        """Sets the digital output value for the specified digital identifier.

        Args:
            port_id: Identifier for one of the 10 output signals:

                * AS5216:

                    * `0`: DO1 = pin 11 at 26-pin connector
                    * `1`: DO2 = pin 2 at 26-pin connector
                    * `2`: DO3 = pin 20 at 26-pin connector
                    * `3`: DO4 = pin 12 at 26-pin connector
                    * `4`: DO5 = pin 3 at 26-pin connector
                    * `5`: DO6 = pin 21 at 26-pin connector
                    * `6`: DO7 = pin 13 at 26-pin connector
                    * `7`: DO8 = pin 4 at 26-pin connector
                    * `8`: DO9 = pin 22 at 26-pin connector
                    * `9`: DO10 = pin 25 at 26-pin connector

                * Mini:

                    * `0`: DO1 = Pin 7 on Micro HDMI = Pin 5 on HDMI terminal
                    * `1`: DO2 = Pin 5 on Micro HDMI = Pin 3 on HDMI Terminal
                    * `2`: DO3 = Pin 3 on Micro HDMI = Pin 1 on HDMI Terminal
                    * `3`: DO4 = Pin 1 on Micro HDMI = Pin 19 on HDMI Terminal
                    * `4`: DO5 = Pin 4 on Micro HDMI = Pin 2 on HDMI Terminal
                    * `5`: DO6 = Pin 2 on Micro HDMI = Pin 14 on HDMI Terminal
                    * `6`: Not used
                    * `7`: Not used
                    * `8`: Not used
                    * `9`: Not used

                * AS7010:

                    * `0`: DO1 =pin 11 at 26-pin connector
                    * `1`: DO2 = pin 2 at 26-pin connector
                    * `2`: DO3 = pin 20 at 26-pin connector
                    * `3`: DO4 = pin 12 at 26-pin connector
                    * `4`: DO5 = pin 3 at 26-pin connector
                    * `5`: DO6 = pin 21 at 26-pin connector
                    * `6`: DO7 = pin 13 at 26-pin connector
                    * `7`: DO8 = pin 4 at 26-pin connector
                    * `8`: DO9 = pin 22 at 26-pin connector
                    * `9`: DO10 = pin 25 at 26-pin connector

            value: The digital value to be set (0 or 1).
        """
        self.sdk.AVS_SetDigOut(self._handle, port_id, value)

    def set_oem_parameter(self, parameter: OemDataType) -> None:
        """Sends the OEM data structure to the spectrometer.

        Args:
            parameter: The OEM data structure.
        """
        self.sdk.AVS_SetOemParameter(self._handle, parameter)

    def set_parameter(self, parameter: DeviceConfigType) -> None:
        """Overwrites the device configuration.

        Please note that [OemDataType][msl.equipment_resources.avantes.avaspec.OemDataType] is part
        of the [DeviceConfigType][msl.equipment_resources.avantes.avaspec.DeviceConfigType] in EEPROM
        (see section 3.5 of DLL manual). Precautions must be taken to prevent OEM data overwrites
        when using this method together with
        [set_oem_parameter][msl.equipment_resources.avantes.avaspec.AvaSpec.set_oem_parameter].

        Args:
            parameter: The device parameters.
        """
        self.sdk.AVS_SetParameter(self._handle, parameter)

    def set_prescan_mode(self, mode: bool) -> None:  # noqa: FBT001
        """If a prescan is set, the first measurement result will be skipped.

        This function is only useful for the AvaSpec-3648 because this detector
        can be operated in prescan mode, or clear-buffer mode (see DLL manual).

        Args:
            mode: If `True`, the first measurement result will be skipped (prescan mode),
                else the detector will be cleared before each new scan (clear-buffer mode).
        """
        self.sdk.AVS_SetPrescanMode(self._handle, mode)

    def set_pwm_out(self, port_id: int, frequency: int, duty_cycle: int) -> None:
        """Selects the PWM functionality for the specified digital output.

        The PWM functionality is not supported on the Mini.

        Args:
            port_id: Identifier for one of the 6 PWM output signals:

                * `0`: DO1 = pin 11 at 26-pin connector
                * `1`: DO2 = pin 2 at 26-pin connector
                * `2`: DO3 = pin 20 at 26-pin connector
                * `4`: DO5 = pin 3 at 26-pin connector
                * `5`: DO6 = pin 21 at 26-pin connector
                * `6`: DO7 = pin 13 at 26-pin connector

            frequency: Desired PWM frequency (500 - 300000) [Hz]. For the AS5216, the frequency of
                outputs 0, 1 and 2 is the same (the last specified frequency is used) and
                also the frequency of outputs 4, 5 and 6 is the same. For the AS7010, you
                can define six different frequencies.
            duty_cycle: Percentage high time in one cycle (0 - 100). For the AS5216, channels 0,
                1 and 2 have a synchronized rising edge, the same holds for channels 4, 5
                and 6. For the AS7010, rising edges are unsynchronized.
        """
        self.sdk.AVS_SetPwmOut(self._handle, port_id, frequency, duty_cycle)

    def set_sensitivity_mode(self, mode: int) -> None:
        """Set the sensitivity mode.

        This method is supported by the following detector types: HAMS9201,
        HAMG9208_512, SU256LSB and SU512LDB with the appropriate firmware version.

        Args:
            mode: 0 for low noise, >0 for high sensitivity
        """
        self.sdk.AVS_SetSensitivityMode(self._handle, mode)

    def set_sync_mode(self, enable: bool) -> None:  # noqa: FBT001
        """Disables/enables support for synchronous measurement.

        Args:
            enable: `False` to disable sync mode, `True` to enable sync mode.
        """
        self.sdk.AVS_SetSyncMode(self._handle, int(bool(enable)))

    def stop_measure(self) -> None:
        """Stops the measurement."""
        self.sdk.AVS_StopMeasure(self._handle)

    def suppress_stray_light(self, factor: float) -> tuple[NDArray[np.double], NDArray[np.double]]:
        """Returns the stray light corrected pixel values of a dark corrected measurement.

        Args:
            factor: Multiplication factor for the stray light algorithm.

        Returns:
            Scope minus dark array, stray light suppressed array.
        """
        x = -9e99
        src = np.full(MAX_NR_PIXELS, x, dtype=np.double)
        dest = np.full(MAX_NR_PIXELS, x, dtype=np.double)
        self.sdk.AVS_SuppressStrayLight(
            self._handle, factor, src.ctypes.data_as(POINTER(c_double)), dest.ctypes.data_as(POINTER(c_double))
        )
        return src[src > x], dest[dest > x]

    def update_eth_devices(self, nmax: int = 16) -> list[BroadcastAnswerType]:
        """Return the number of Ethernet devices that are connected to the computer.

        Internally checks the list of connected Ethernet devices and returns the number of devices attached.

        Args:
            nmax: The maximum number of devices that can be found.

        Returns:
            The information about the devices.
        """
        size = nmax * sizeof(BroadcastAnswerType)
        required_size = c_uint32()
        types = (BroadcastAnswerType * nmax)()
        n = self.sdk.AVS_UpdateETHDevices(size, required_size, types)
        return [types[i] for i in range(n)]

    def update_usb_devices(self) -> int:
        """Return the number of USB devices that are connected to the computer.

        Internally checks the list of connected USB devices and returns the number of devices attached.

        Returns:
            The number of devices found.
        """
        return int(self.sdk.AVS_UpdateUSBDevices())

    def use_high_res_adc(self, enable: bool) -> None:  # noqa: FBT001
        """Enable the 16-bit AD converter.

        When using the 16 bit ADC in full High Resolution mode (0..65535), please note that the
        irradiance intensity calibration, as well as the nonlinearity calibration are based on the 14bit
        ADC range. Therefore, if using the nonlinearity correction or irradiance calibration in your
        own software using the High Resolution mode, you need to apply the additional correction
        with ADCFactor (= 4.0), as explained in detail in section 4.6.1 and 4.6.3 of the manual.

        Args:
            enable: If `True` use a 16-bit AD converter, otherwise use a 14-bit ADC.
        """
        self.sdk.AVS_UseHighResAdc(self._handle, bool(enable))

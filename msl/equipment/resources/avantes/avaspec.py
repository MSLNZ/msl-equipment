"""
Wrapper around the ``avaspec.dll`` SDK from Avantes.

The wrapper was written using v9.7.0.0 of the SDK.
"""
from ctypes import *
from enum import IntEnum

import numpy as np
from msl.loadlib import IS_WINDOWS, LoadLibrary

from msl.equipment.connection_sdk import ConnectionSDK
from msl.equipment.exceptions import AvantesError
from msl.equipment.resources import register


def get_list(path='avaspecx64.dll', port_id=-1, nmax=16):
    """Returns device information for each spectrometer that is connected.

    Parameters
    ----------
    path : :class:`str`
        The path to the Avantes SDK.
    port_id : :class:`int`
        ID of port to be used. One of:

            * -1: Use both Ethernet (AS7010) and USB ports
            * 0: Use USB port
            * 1..255: Not supported in v9.7 of the SDK
            * 256: Use Ethernet port (AS7010)
    nmax : :class:`int`, optional
        The maximum number of devices that can be in the list.

    Returns
    -------
    :class:`list` of :class:`.AvsIdentityType`
        The information about the devices.
    """
    lib = LoadLibrary(path, 'windll').lib

    ret = lib.AVS_Init(port_id)
    if ret == 0:
        raise AvantesError('No Avantes devices were found')

    size = nmax * sizeof(AvsIdentityType)
    required_size = c_uint32()
    types = (AvsIdentityType * nmax)()

    lib.AVS_GetList.argtypes = [c_uint32, POINTER(c_uint32), POINTER(AvsIdentityType)]
    n = lib.AVS_GetList(size, required_size, types)
    if n < 0:
        error_name, msg = ERROR_CODES.get(n, ('UNKNOWN_ERROR', 'Unknown error'))
        raise AvantesError('{}: {}'.format(error_name, msg))

    return [types[i] for i in range(n)]


@register(manufacturer=r'Avantes', model=r'.')
class AvaSpec(ConnectionSDK):

    def __init__(self, record):
        """Wrapper around the ``avaspec.dll`` SDK from Avantes.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for an Avantes connection supports the following key-value pairs in the
        :ref:`connections_database`::

            'port_id': int, One of -1 (Ethernet+USB), 0 (USB) or 256 (Ethernet) [default: -1]
            'activate': bool, Whether to automatically activate the connection [default: True]

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        self._handle = None
        super(AvaSpec, self).__init__(record, 'windll')
        self.set_exception_class(AvantesError)

        self.MeasConfigType = MeasConfigType  #: :class:`MeasConfigType`
        self.OemDataType = OemDataType  #: :class:`OemDataType`
        self.DeviceConfigType = DeviceConfigType  #: :class:`DeviceConfigType`

        functions = {
            'AVS_Init': (c_int32, self._err_check,
                [('a_Port', c_int16)]),
            'AVS_Done': (c_int32, self._err_check,
                []),
            'AVS_GetNrOfDevices': (c_int32, self.log_errcheck,
                []),
            'AVS_UpdateUSBDevices': (c_int32, self.log_errcheck,
                []),
            'AVS_UpdateETHDevices': (c_int32, self._err_check,
                [('a_ListSize', c_uint32),
                 ('a_pRequiredSize', POINTER(c_uint32)),
                 ('a_pList', POINTER(BroadcastAnswerType))]),
            'AVS_GetList': (c_int32, self._err_check,
                [('a_ListSize', c_uint32),
                 ('a_pRequiredSize', POINTER(c_uint32)),
                 ('a_pList', POINTER(AvsIdentityType))]),
            'AVS_Activate': (c_int32, self._err_check,
                [('a_pDeviceId', POINTER(AvsIdentityType))]),
            'AVS_ActivateConn': (c_int32, self._err_check,
                [('a_pDeviceId', POINTER(AvsIdentityType))]),
            'AVS_ActivateConnCb': (c_int32, self._err_check,
                [('a_pDeviceId', POINTER(AvsIdentityType))]),
            'AVS_Deactivate': (c_bool, self._check_bool,
                [('a_hDevice', c_int32)]),
            'AVS_GetHandleFromSerial': (c_int32, self._err_check,
                [('a_pSerial', c_char_p)]),
            'AVS_GetStatusBySerial': (c_int32, self._err_check,
                [('a_pSerial', c_char_p),
                 ('a_status', POINTER(c_int32))]),
            'AVS_Register': (c_bool, self._check_bool,
                [('a_Hwnd', c_void_p)]),
            'AVS_Measure': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_hWnd', c_void_p),
                 ('a_Nmsr', c_int16)]),
            'AVS_MeasureCallback': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('__Done', MeasureCallback),
                 ('a_Nmsr', c_int16)]),
            'AVS_PrepareMeasure': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pMeasConfig', POINTER(MeasConfigType))]),
            'AVS_StopMeasure': (c_int32, self._err_check,
                [('a_hDevice', c_int32)]),
            'AVS_PollScan': (c_int32, self._err_check,
                [('a_hDevice', c_int32)]),
            'AVS_GetScopeData': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pTimeLabel', POINTER(c_uint32)),
                 ('a_pSpectrum', POINTER(c_double))]),
            'AVS_GetSaturatedPixels': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pSaturated', POINTER(c_ubyte))]),
            'AVS_GetLambda': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pWaveLength', POINTER(c_double))]),
            'AVS_GetNumPixels': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pNumPixels', POINTER(c_uint16))]),
            'AVS_GetParameter': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_Size', c_uint32),
                 ('a_pRequiredSize', POINTER(c_uint32)),
                 ('a_pDeviceParm', POINTER(DeviceConfigType))]),
            'AVS_SetParameter': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pDeviceParm', POINTER(DeviceConfigType))]),
            'AVS_GetVersionInfo': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pFPGAVersion', c_char_p),
                 ('a_pFirmwareVersion', c_char_p),
                 ('a_pDLLVersion', c_char_p)]),
            'AVS_GetDLLVersion': (c_int32, self._err_check,
                [('a_pVersionString', c_char_p)]),
            'AVS_SetSyncMode': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_Enable', c_ubyte)]),
            'AVS_SetPrescanMode': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_Prescan', c_bool)]),
            'AVS_UseHighResAdc': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_Enable', c_bool)]),
            'AVS_GetAnalogIn': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_AnalogInId', c_ubyte),
                 ('a_pAnalogIn', POINTER(c_float))]),
            'AVS_GetDigIn': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_DigInId', c_ubyte),
                 ('a_pDigIn', POINTER(c_ubyte))]),
            'AVS_SetAnalogOut': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_PortId', c_ubyte),
                 ('a_Value', c_float)]),
            'AVS_SetDigOut': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_PortId', c_ubyte),
                 ('a_Status', c_ubyte)]),
            'AVS_SetPwmOut': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_PortId', c_ubyte),
                 ('a_Freq', c_ulong),
                 ('a_Duty', c_ubyte)]),
            'AVS_GetDarkPixelData': (c_int32, self._check_bool,
                [('a_hDevice', c_int32),
                 ('a_pDarkData', POINTER(c_double))]),
            'AVS_GetComPortName': (c_int32, self._check_bool,
                [('a_pDeviceId', POINTER(AvsIdentityType)),
                 ('a_pIp', c_char_p),
                 ('a_size', POINTER(c_int32))]),
            'AVS_GetComType': (c_int32, self._err_check,
                [('a_pDeviceId', POINTER(AvsIdentityType)),
                 ('a_type', POINTER(c_int32))]),
            'AVS_SetSensitivityMode': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_SensitivityMode', c_uint32)]),
            'AVS_GetIpConfig': (c_int32, self._check_bool,
                [('a_hDevice', c_int32),
                 ('a_Data', POINTER(EthernetSettingsType))]),
            'AVS_SuppressStrayLight': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_Multifactor', c_float),
                 ('a_pSrcSpectrum', POINTER(c_double)),
                 ('a_pDestSpectrum', POINTER(c_double))]),
            'AVS_Heartbeat': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pHbReq', POINTER(c_uint32)),
                 ('a_pHbResp', POINTER(HeartbeatRespType))]),
            'AVS_ResetDevice': (c_int32, self._err_check,
                [('a_hDevice', c_int32)]),
            'AVS_GetOemParameter': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pOemData', POINTER(OemDataType))]),
            'AVS_SetOemParameter': (c_int32, self._err_check,
                [('a_hDevice', c_int32),
                 ('a_pOemData', POINTER(OemDataType))]),
        }

        for key, value in functions.items():
            attr = getattr(self.sdk, key)
            attr.restype, attr.errcheck = value[:2]
            attr.argtypes = [typ for _, typ in value[2]]

        props = record.connection.properties
        self.init(props.get('port_id', -1))
        if props.get('activate', True):
            self.activate()

    def _err_check(self, result, func, arguments):
        self.log_errcheck(result, func, arguments)
        if result < 0:
            error_name, msg = ERROR_CODES.get(result, ('UNKNOWN_ERROR', 'Unknown error'))
            self.raise_exception('{}: {}'.format(error_name, msg))
        return result

    def _check_bool(self, result, func, arguments):
        self.log_errcheck(result, func, arguments)
        if not result:
            self.raise_exception('The {} function returned False'.format(func))

    def activate(self):
        """Activates the spectrometer for communication.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        out = get_list(path=self.path)
        if len(out) < 1:
            self.raise_exception('Cannot activate. No devices found.')
        for item in out:
            if item.SerialNumber.decode() == self.equipment_record.serial:
                self._handle = self.sdk.AVS_Activate(item)
                return
        self.raise_exception('Did not find the Avantes serial number {!r}'
                             'in the list of devices.'.format(self.equipment_record.serial))

    def deactivate(self):
        """Closes communication with the spectrometer."""
        if self._handle:
            self.sdk.AVS_Deactivate(self._handle)
            self._handle = None

    def get_analog_in(self, analog_id):
        """Get the status of the specified analog input.

        Parameters
        ----------
        analog_id : :class:`int`
            The identifier of the analog input to get.

            * AS5216:

                * 0 = thermistor on optical bench (NIR 2.0 / NIR2.2 / NIR 2.5 / TEC)
                * 1 = 1V2
                * 2 = 5VIO
                * 3 = 5VUSB
                * 4 = AI2 = pin 18 at 26-pins connector
                * 5 = AI1 = pin 9 at 26-pins connector
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
                * 4 = AI2 = pin 18 at 26-pins connector
                * 5 = AI1 = pin 9 at 26-pins connector
                * 6 = digital temperature sensor, returns degrees Celsius, not Volts
                * 7 = Not used

        Returns
        -------
        :class:`float`
            The analog input value [Volts or degrees Celsius].

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        ain = c_float()
        self.sdk.AVS_GetAnalogIn(self._handle, analog_id, ain)
        return ain.value

    def get_com_port_name(self):
        """Get the IP address of the device.

        Returns
        -------
        :class:`str`
            The IP address of the device.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        size = c_int32(1023)
        device_id = AvsIdentityType()
        device_id.SerialNumber = self.equipment_record.serial.encode()
        name = create_string_buffer(size.value)
        self.sdk.AVS_GetComPortName(device_id, name, size)
        return name.value.decode()

    def get_com_type(self):
        """Get the communication protocol.

        Returns
        -------
        :class:`str`
            The communication type as defined below:

            * RS232 = 0
            * USB5216 = 1
            * USBMINI = 2
            * USB7010 = 3
            * ETH7010 = 4
            * UNKNOWN = -1

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        device_id = AvsIdentityType()
        device_id.SerialNumber = self.equipment_record.serial.encode()
        typ = c_int32(-1)
        self.sdk.AVS_GetComType(device_id, typ)
        return typ.value

    def get_dark_pixel_data(self):
        """Get the optically black pixel values of the last performed measurement.

        You must call :meth:`get_data` before you call this method.

        Returns
        -------
        :class:`numpy.ndarray`
            The dark pixels.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        # from the docs the maximum size is size=18 for the AvaSpec-2048-USB2 and AvaSpec-2048L-USB2
        values = np.zeros(32, dtype=np.double)  # make it bigger than 18
        self.sdk.AVS_GetDarkPixelData(self._handle, values.ctypes.data_as(POINTER(c_double)))
        return values[values > 0]

    def get_dll_version(self):
        """Get the DLL version number.

        Returns
        -------
        :class:`str`
            The DLL version number
        """
        version = create_string_buffer(255)
        self.sdk.AVS_GetDLLVersion(version)
        return version.value.decode()

    def get_digital_in(self, digital_id):
        """Get the status of the specified digital input.

        Parameters
        ----------
        digital_id : :class:`int`
            The identifier of the digital input to get.

            * AS5216:

                * 0 = DI1 = Pin 24 at 26-pins connector
                * 1 = DI2 = Pin 7 at 26-pins connector
                * 2 = DI3 = Pin 16 at 26-pins connector

            * Mini:

                * 0 = DI1 = Pin 7 on Micro HDMI = Pin 5 on HDMI terminal
                * 1 = DI2 = Pin 5 on Micro HDMI = Pin 3 on HDMI Terminal
                * 2 = DI3 = Pin 3 on Micro HDMI = Pin 1 on HDMI Terminal
                * 3 = DI4 = Pin 1 on Micro HDMI = Pin 19 on HDMI Terminal
                * 4 = DI5 = Pin 4 on Micro HDMI = Pin 2 on HDMI Terminal
                * 5 = DI6 = Pin 2 on Micro HDMI = Pin 14 on HDMI Terminal

            * AS7010:

                * 0 = DI1 = Pin 24 at 26-pins connector
                * 1 = DI2 = Pin 7 at 26-pins connector
                * 2 = DI3 = Pin 16 at 26-pins

        Returns
        -------
        :class:`int`
            The digital input value.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        din = c_ubyte()
        self.sdk.AVS_GetDigIn(self._handle, digital_id, din)
        return din.value

    def get_handle_from_serial(self, serial=None):
        """Get the handle ID for the specified serial number.

        Parameters
        ----------
        serial : :class:`str`
            The serial number. Default is to get the status for this object.

        Returns
        -------
        :class:`int`
            The handle.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        if serial is None:
            serial = self.equipment_record.serial.encode()
        elif not isinstance(serial, bytes):
            serial = serial.encode()
        return self.sdk.AVS_GetHandleFromSerial(serial)

    def get_status_by_serial(self, serial=None):
        """Get the handle ID for the specified serial number.

        Parameters
        ----------
        serial : :class:`str`, optional
            The serial number. Default is to get the status for this object.

        Returns
        -------
        :class:`int`
            The status.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        if serial is None:
            serial = self.equipment_record.serial.encode()
        elif not isinstance(serial, bytes):
            serial = serial.encode()
        status = c_int32()
        self.sdk.AVS_GetStatusBySerial(serial, status)
        return status.value

    def done(self):
        """Closes communication and releases internal storage."""
        self.sdk.AVS_Done()

    def disconnect(self):
        """Closes communication with the spectrometer."""
        self.deactivate()
        self.done()

    def get_ip_config(self):
        """Retrieve IP settings from the spectrometer.

        Use this function to read the Ethernet settings of the spectrometer, without
        having to read the complete device configuration structure.

        Returns
        -------
        :class:`.EthernetSettingsType`
            The Ethernet settings of the spectrometer.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        eth = EthernetSettingsType()
        self.sdk.AVS_GetIpConfig(self._handle, eth)
        return eth

    def get_lambda(self):
        """Returns the wavelength values corresponding to the pixels if available.

        Returns
        -------
        :class:`numpy.ndarray`
            The wavelength value of each pixel.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        values = np.zeros(MAX_NR_PIXELS, dtype=np.double)
        self.sdk.AVS_GetLambda(self._handle, values.ctypes.data_as(POINTER(c_double)))
        return values[values > 0]

    def get_num_devices(self):
        """Scans for attached devices and returns the number of devices detected.

        Deprecated function, replaced by :meth:`.update_usb_devices`. The
        functionality is identical.

        Returns
        -------
        :class:`int`
            The number of devices found.
        """
        return self.sdk.AVS_GetNrOfDevices()

    def get_oem_parameter(self):
        """Returns the OEM data structure available on the spectrometer.

        Returns
        -------
        :class:`.OemDataType`
            The OEM parameters.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        odt = OemDataType()
        self.sdk.AVS_GetOemParameter(self._handle, odt)
        return odt

    def get_parameter(self):
        """Returns the device information of the spectrometer.

        Returns
        -------
        :class:`.DeviceConfigType`
            The device parameters.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        dct = DeviceConfigType()
        required_size = c_uint32()
        self.sdk.AVS_GetParameter(self._handle, sizeof(dct), required_size, dct)
        return dct

    def get_saturated_pixels(self):
        """Returns, for each pixel, if a pixel was saturated (1) or not (0).

        Returns
        -------
        :class:`numpy.ndarray`
            The saturation state of each pixel.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        values = np.ones(MAX_NR_PIXELS, dtype=np.uint8) * 9
        self.sdk.AVS_GetSaturatedPixels(self._handle, values.ctypes.data_as(POINTER(c_ubyte)))
        return values[values < 9]

    def get_version_info(self):
        """Returns software version information.

        Returns
        -------
        :class:`str`
            FPGA software version.
        :class:`str`
            Firmware version.
        :class:`str`
            DLL version.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        fpga = (c_ubyte * 16)()
        fm = (c_ubyte * 16)()
        dll = (c_ubyte * 16)()
        self.sdk.AVS_GetVersionInfo(self._handle, fpga, fm, dll)
        return [string_at(addressof(obj)).decode() for obj in [fpga, fm, dll]]

    def get_data(self):
        """Returns the pixel values of the last performed measurement.

        Returns
        -------
        :class:`int`
            Tick count the last pixel of the spectrum was received by the microcontroller.
            Ticks are in 10 microsecond units since the spectrometer started.
        :class:`numpy.ndarray`
            The pixel values.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        ticks = c_uint32()
        values = np.ones(MAX_NR_PIXELS, dtype=np.double) * -1.0
        self.sdk.AVS_GetScopeData(self._handle, ticks, values.ctypes.data_as(POINTER(c_double)))
        return ticks.value, values[values > -1.0]

    def get_num_pixels(self):
        """Returns the number of pixels of a spectrometer.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        n = c_uint16()
        self.sdk.AVS_GetNumPixels(self._handle, n)
        return n.value

    def heartbeat(self, req_type):
        """Monitor the (heartbeat) functions of the spectrometer.

        This function applies only to the AS7010 platform. See the DLL manual for more details.

        Parameters
        ----------
        req_type : :class:`int`
            The heartbeat request values used to control heartbeat functions.

        Returns
        -------
        :class:`.HeartbeatRespType`
            The heartbeat response structure received from the spectrometer.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        resp = HeartbeatRespType()
        self.sdk.AVS_Heartbeat(self._handle, req_type, resp)
        return resp

    def init(self, port_id):
        """Initializes the communication interface with the spectrometers and the internal data structures.

        For Ethernet devices this function will create a list of available Ethernet spectrometers
        within all the network interfaces of the host.

        Parameters
        ----------
        port_id : :class:`int`
            ID of port to be used. One of:

                * -1: Use both Ethernet (AS7010) and USB ports
                * 0: Use USB port
                * 1..255: Not supported in v9.7 of the SDK
                * 256: Use Ethernet port (AS7010)

        Returns
        -------
        :class:`int`
            On success, the number of connected or found devices.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If no devices were found.
        """
        ret = self.sdk.AVS_Init(port_id)
        if ret == 0:
            self.raise_exception('No Avantes devices were found')
        return ret

    def measure(self, num_measurements, window_handle=None):
        """Starts measurement on the spectrometer.

        Parameters
        ----------
        num_measurements : :class:`int`
            Number of measurements to acquire. Use -1 to measure continuously until
            :meth:`.stop_measure` is called.
        window_handle : :class:`ctypes.c_void_p`, optional
            Window handle to notify application measurement result data is available.
            The DLL sends a message to the window with command: `WM_MEAS_READY`, with
            `SUCCESS` (``0``), the number of scans that were saved in RAM (if `m_StoreToRAM`
            parameter > 0, see :class:`ControlSettingsType`), or `INVALID_MEAS_DATA`
            as `WPARM` value and `a_hDevice` as `LPARM` value. Set this value to :data:`None`
            if a callback is not needed.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_Measure(self._handle, window_handle, num_measurements)

    def measure_callback(self, num_measurements, callback=None):
        """Starts measurement on the spectrometer.

        Parameters
        ----------
        num_measurements : :class:`int`
            Number of measurements to acquire. Use -1 to measure continuously until
            :meth:`.stop_measure` is called.
        callback : :attr:`MeasureCallback`, optional
            A function to notify application measurement result data is available.
            The DLL will call the given function to notify a measurement is ready and pass
            two parameters. The first parameter is a reference to the DLL handle. The
            second parameter is a reference to an integer value: `SUCCESS` (``0``) if a new
            scan is available, or the number of scans that were saved in RAM (if `m_StoreToRAM`
            parameter > 0, see :class:`ControlSettingsType`), or `INVALID_MEAS_DATA` (``-8``).
            Set this value to :data:`None` if a callback is not needed.

        Examples
        --------
        .. code-block:: python

            from msl.equipment.resources.avantes import MeasureCallback

            @MeasureCallback
            def avantes_callback(handle, info):
                print('The DLL handle is:', handle.contents.value)
                if info.contents.value == 0:  # equals 0 if everything is okay
                    print('  callback data:', ava.get_data())

            # here "ava" is a reference to the AvaSpec class
            ava.measure_callback(-1, avantes_callback)

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_MeasureCallback(self._handle, callback, num_measurements)

    def poll_scan(self):
        """Determines if new measurement results are available.

        Returns
        -------
        :class:`int`
            Whether there is a scan available: 0 (No) or 1 (Yes).

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        return self.sdk.AVS_PollScan(self._handle)

    def prepare_measure(self, config):
        """Prepares measurement on the spectrometer using the specified measurement configuration.

        Parameters
        ----------
        config : :class:`.MeasConfigType`
            The measurement configuration.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        if not isinstance(config, MeasConfigType):
            self.raise_exception('Must pass in a MeasConfigType object')
        self.sdk.AVS_PrepareMeasure(self._handle, config)

    def register(self, handle):
        """Installs an application windows handle to which device
        attachment/removal messages have to be sent.

        Parameters
        ----------
        handle : :class:`ctypes.c_void_p`
            Application window handle.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_Register(handle)

    def reset_device(self):
        """Performs a hard reset on the given spectrometer.

        This function only works with the AS7010 platform.

        During reset of the spectrometer, all spectrometer HW modules (microprocessor
        and USB controller) will be reset at once. The spectrometer will start its reset
        procedure right after sending the command response back to the host.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_ResetDevice(self._handle)

    def set_analog_out(self, port_id, value):
        """Sets the analog output value for the specified analog identifier.

        Parameters
        ----------
        port_id : :class:`int`
            Identifier for one of the two output signals:

            * AS5216:

                * 0 = AO1 = pin 17 at 26-pins connector
                * 1 = AO2 = pin 26 at 26-pins connector

            * Mini:

                * 0 = AO1 = Pin 12 on Micro HDMI = Pin 10 on HDMI terminal
                * 1 = AO2 = Pin 14 on Micro HDMI = Pin 12 on HDMI terminal

            * AS7010:

                * 0 = AO1 = pin 17 at 26-pins connector
                * 1 = AO2 = pin 26 at 26-pins connector

        value : :class:`float`
            DAC value to be set in Volts (internally an 8-bits DAC is used) with range 0 - 5.0V.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_SetAnalogOut(self._handle, port_id, value)

    def set_digital_out(self, port_id, value):
        """Sets the digital output value for the specified digital identifier.

        Parameters
        ----------
        port_id : :class:`int`
            Identifier for one of the 10 output signals:

            * AS5216:

                * 0 = DO1 = pin 11 at 26-pins connector
                * 1 = DO2 = pin 2 at 26-pins connector
                * 2 = DO3 = pin 20 at 26-pins connector
                * 3 = DO4 = pin 12 at 26-pins connector
                * 4 = DO5 = pin 3 at 26-pins connector
                * 5 = DO6 = pin 21 at 26-pins connector
                * 6 = DO7 = pin 13 at 26-pins connector
                * 7 = DO8 = pin 4 at 26-pins connector
                * 8 = DO9 = pin 22 at 26-pins connector
                * 9 = DO10 = pin 25 at 26-pins connector

            * Mini:

                * 0 = DO1 = Pin 7 on Micro HDMI = Pin 5 on HDMI terminal
                * 1 = DO2 = Pin 5 on Micro HDMI = Pin 3 on HDMI Terminal
                * 2 = DO3 = Pin 3 on Micro HDMI = Pin 1 on HDMI Terminal
                * 3 = DO4 = Pin 1 on Micro HDMI = Pin 19 on HDMI Terminal
                * 4 = DO5 = Pin 4 on Micro HDMI = Pin 2 on HDMI Terminal
                * 5 = DO6 = Pin 2 on Micro HDMI = Pin 14 on HDMI Terminal
                * 6 = Not used
                * 7 = Not used
                * 8 = Not used
                * 9 = Not used

            * AS7010:

                * 0 = DO1 =pin 11 at 26-pins connector
                * 1 = DO2 = pin 2 at 26-pins connector
                * 2 = DO3 = pin 20 at 26-pins connector
                * 3 = DO4 = pin 12 at 26-pins connector
                * 4 = DO5 = pin 3 at 26-pins connector
                * 5 = DO6 = pin 21 at 26-pins connector
                * 6 = DO7 = pin 13 at 26-pins connector
                * 7 = DO8 = pin 4 at 26-pins connector
                * 8 = DO9 = pin 22 at 26-pins connector
                * 9 = DO10 = pin 25 at 26-pins connector

        value : :class:`int`
            The value to be set (0 or 1).

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_SetDigOut(self._handle, port_id, value)

    def set_oem_parameter(self, parameter):
        """Sends the OEM data structure to the spectrometer.

        Parameters
        ----------
        parameter : :class:`.OemDataType`
            The OEM data structure.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        if not isinstance(parameter, OemDataType):
            self.raise_exception('Must pass in an OemDataType object')
        self.sdk.AVS_SetOemParameter(self._handle, parameter)

    def set_parameter(self, parameter):
        """Overwrites the device configuration.

        Please note that :class:`OemDataType` is part of the DeviceConfigType in EEPROM (see
        section 3.5 of DLL manual). Precautions must be taken to prevent OEM data overwrites
        when using :meth:`.set_parameter` method together with :meth:`.set_oem_parameter`.

        Parameters
        ----------
        parameter : :class:`.DeviceConfigType`
            The device parameters.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        if not isinstance(parameter, DeviceConfigType):
            self.raise_exception('Must pass in a DeviceConfigType object')
        self.sdk.AVS_SetParameter(self._handle, parameter)

    def set_prescan_mode(self, boolean):
        """If a prescan is set, the first measurement result will be skipped.

        This function is only useful for the AvaSpec-3648 because this detector
        can be operated in prescan mode, or clear-buffer mode (see DLL manual).

        Parameters
        ----------
        boolean : :class:`bool`
            If :data:`True`, the first measurement result will be skipped (prescan mode),
            else the detector will be cleared before each new scan (clear-buffer mode).

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_SetPrescanMode(self._handle, boolean)

    def set_pwm_out(self, port_id, frequency, duty_cycle):
        """Selects the PWM functionality for the specified digital output.

        The PWM functionality is not supported on the Mini.

        Parameters
        ----------
        port_id : :class:`int`
            Identifier for one of the 6 PWM output signals:

            * 0 = DO1 = pin 11 at 26-pins connector
            * 1 = DO2 = pin 2 at 26-pins connector
            * 2 = DO3 = pin 20 at 26-pins connector
            * 4 = DO5 = pin 3 at 26-pins connector
            * 5 = DO6 = pin 21 at 26-pins connector
            * 6 = DO7 = pin 13 at 26-pins connector

        frequency : :class:`int`
            Desired PWM frequency (500 - 300000) [Hz]. For the AS5216, the frequency of
            outputs 0, 1 and 2 is the same (the last specified frequency is used) and
            also the frequency of outputs 4, 5 and 6 is the same. For the AS7010, you
            can define six different frequencies.
        duty_cycle : :class:`int`
            Percentage high time in one cycle (0 - 100). For the AS5216, channels 0,
            1 and 2 have a synchronized rising edge, the same holds for channels 4, 5
            and 6. For the AS7010, rising edges are unsynchronized.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_SetPwmOut(self._handle, port_id, frequency, duty_cycle)

    def set_sensitivity_mode(self, value):
        """Set the sensitivity mode.

        This method is supported by the following detector types: HAMS9201,
        HAMG9208_512, SU256LSB and SU512LDB with the appropriate firmware version.

        Parameters
        ----------
        value : :class:`int`
            0 for low noise, >0 for high sensitivity

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_SetSensitivityMode(self._handle, value)

    def set_sync_mode(self, enable):
        """Disables/enables support for synchronous measurement.

        Parameters
        ----------
        enable : :class:`bool`
            :data:`False` to disable sync mode, :data:`True` to enable sync mode.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_SetSyncMode(self._handle, int(bool(enable)))

    def stop_measure(self):
        """Stops the measurement.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_StopMeasure(self._handle)

    def suppress_stray_light(self, factor):
        """Returns the stray light corrected pixel values of a dark corrected measurement.

        Parameters
        ----------
        factor : :class:`float`
            Multiplication factor for the stray light algorithm.

        Returns
        -------
        :class:`numpy.ndarray`
            Scope minus dark.
        :class:`numpy.ndarray`
            Stray light suppressed.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        x = -9e99
        src = np.ones(MAX_NR_PIXELS, dtype=np.double) * x
        dest = np.ones(MAX_NR_PIXELS, dtype=np.double) * x
        self.sdk.AVS_SuppressStrayLight(
            self._handle,
            factor,
            src.ctypes.data_as(POINTER(c_double)),
            dest.ctypes.data_as(POINTER(c_double))
        )
        return src[src > x], dest[dest > x]

    def update_eth_devices(self, nmax=16):
        """Return the number of Ethernet devices that are connected to the computer.

        Internally checks the list of connected Ethernet devices and returns the number of devices
        attached. If the :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        attribute contains a key ``'port_id'`` with a value of ``-1`` then the returned value
        also includes the number of USB devices.

        Parameters
        ----------
        nmax : :class:`int`, optional
            The maximum number of devices that can be found.

        Returns
        -------
        :class:`list` of :class:`.BroadcastAnswerType`
            The information about the devices.
        """
        size = nmax * sizeof(BroadcastAnswerType)
        required_size = c_uint32()
        types = (BroadcastAnswerType * nmax)()
        n = self.sdk.AVS_UpdateETHDevices(size, required_size, types)
        return [types[i] for i in range(n)]

    def update_usb_devices(self):
        """Return the number of USB devices that are connected to the computer.

        Internally checks the list of connected USB devices and returns the number of devices
        attached. If the :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        attribute contains a key ``'port_id'`` with a value of ``-1`` then the returned value
        also includes the number of Ethernet devices.

        Returns
        -------
        :class:`int`
            The number of devices found.
        """
        return self.sdk.AVS_UpdateUSBDevices()

    def use_high_res_adc(self, enable):
        """Enable the 16-bit AD converter.

        When using the 16 bit ADC in full High Resolution mode (0..65535), please note that the
        irradiance intensity calibration, as well as the nonlinearity calibration are based on the 14bit
        ADC range. Therefore, if using the nonlinearity correction or irradiance calibration in your
        own software using the High Resolution mode, you need to apply the additional correction
        with ADCFactor (= 4.0), as explained in detail in section 4.6.1 and 4.6.3 of the manual.

        Parameters
        ----------
        enable : :class:`bool`
            If :data:`True` use a 16-bit AD converter, otherwise use a 14-bit ADC.

        Raises
        ------
        :class:`~msl.equipment.exceptions.AvantesError`
            If there was an error.
        """
        self.sdk.AVS_UseHighResAdc(self._handle, bool(enable))


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
    -1: ('ERR_INVALID_PARAMETER',
         'Function called with invalid parameter value.'),
    -2: ('ERR_OPERATION_NOT_SUPPORTED',
         'Function not supported (e.g. use 16bit ADC mode with 14bit ADC hardware)'),
    -3: ('ERR_DEVICE_NOT_FOUND',
         'Opening communication failed or time-out during communication occurred.'),
    -4: ('ERR_INVALID_DEVICE_ID',
         'AvsHandle is unknown in the DLL'),
    -5: ('ERR_OPERATION_PENDING',
         'Function is called while result of previous call to AVS_Measure() is not received yet'),
    -6: ('ERR_TIMEOUT',
         'No answer received from device'),
    -7: ('Reserved',
         ''),
    -8: ('ERR_INVALID_MEAS_DATA',
         'No measurement data is received at the point AVS_GetScopeData() is called'),
    -9: ('ERR_INVALID_SIZE',
         'Allocated buffer size too small'),
    -10: ('ERR_INVALID_PIXEL_RANGE',
          'Measurement preparation failed because pixel range is invalid'),
    -11: ('ERR_INVALID_INT_TIME',
          'Measurement preparation failed because integration time is invalid (for selected sensor)'),
    -12: ('ERR_INVALID_COMBINATION',
          'Measurement preparation failed because of an invalid combination of parameters, e.g. integration time of 600000 and Navg > 5000'),
    -13: ('Reserved',
          ''),
    -14: ('ERR_NO_MEAS_BUFFER_AVAIL',
          'Measurement preparation failed because no measurement buffers available'),
    -15: ('ERR_UNKNOWN',
          'Unknown error reason received from spectrometer'),
    -16: ('ERR_COMMUNICATION',
          'Error in communication or Ethernet connection failure'),
    -17: ('ERR_NO_SPECTRA_IN_RAM',
          'No more spectra available in RAM, all read or measurement not started yet'),
    -18: ('ERR_INVALID_DLL_VERSION',
          'DLL version information could not be retrieved'),
    -19: ('ERR_NO_MEMORY',
          'Memory allocation error in the DLL'),
    -20: ('ERR_DLL_INITIALISATION',
          'Function called before AVS_Init() is called'),
    -21: ('ERR_INVALID_STATE',
          'Function failed because AvaSpec is in wrong state, e.g. AVS_Measure() without calling AVS_PrepareMeasurement() first'),
    -22: ('ERR_INVALID_REPLY',
          'Reply is not a recognized protocol message'),
    -23: ('Reserved',
          ''),
    -24: ('ERR_ACCESS',
          'Error occurred while opening a bus device on the host, e.g. USB device access denied due to user rights'),
    -100: ('ERR_INVALID_PARAMETER_NR_PIXEL',
           'NrOfPixel in Device data incorrect'),
    -101: ('ERR_INVALID_PARAMETER_ADC_GAIN',
           'Gain Setting Out of Range'),
    -102: ('ERR_INVALID_PARAMETER_ADC_OFFSET',
           'OffSet Setting Out of Range'),
    -110: ('ERR_INVALID_MEASPARAM_AVG_SAT2',
           'Use of Saturation Detection Level 2 is not compatible with the Averaging function'),
    -111: ('ERR_INVALID_MEASPARAM_AVG_RAM',
           'Use of Averaging is not compatible with the StoreToRam function'),
    -112: ('ERR_INVALID_MEASPARAM_SYNC_RAM',
           'Use of the Synchronize setting is not compatible with the StoreToRam function'),
    -113: ('ERR_INVALID_MEASPARAM_LEVEL_RAM',
           'Use of Level Triggering is not compatible with the StoreToRam function'),
    -114: ('ERR_INVALID_MEASPARAM_SAT2_RAM',
           'Use of Saturation Detection Level 2 Parameter is not compatible with the StoreToRam function'),
    -115: ('ERR_INVALID_MEASPARAM_FWVER_RAM',
           'The StoreToRam function is only supported with firmware version 0.20.0.0 or later.'),
    -116: ('ERR_INVALID_MEASPARAM_DYNDARK',
           'Dynamic Dark Correction not supported'),
    -120: ('ERR_NOT_SUPPORTED_BY_SENSOR_TYPE',
           'Use of AVS_SetSensitivityMode() not supported by detector type'),
    -121: ('ERR_NOT_SUPPORTED_BY_FW_VER',
           'Use of AVS_SetSensitivityMode() not supported by firmware version'),
    -122: ('ERR_NOT_SUPPORTED_BY_FPGA_VER',
           'Use of AVS_SetSensitivityMode() not supported by FPGA version'),
    -140: ('ERR_SL_CALIBRATION_NOT_AVAILABLE',
           'Spectrometer was not calibrated for stray light correction'),
    -141: ('ERR_SL_STARTPIXEL_NOT_IN_RANGE',
           'Incorrect start pixel found in EEPROM'),
    -142: ('ERR_SL_ENDPIXEL_NOT_IN_RANGE',
           'Incorrect end pixel found in EEPROM'),
    -143: ('ERR_SL_STARTPIX_GT_ENDPIX',
           'Incorrect start or end pixel found in EEPROM'),
    -144: ('ERR_SL_MFACTOR_OUT_OF_RANGE',
           'Factor should be in range 0.0 - 4.0'),
}


class DeviceStatus(IntEnum):
    """DeviceStatus enum."""
    UNKNOWN = 0
    USB_AVAILABLE = 1
    USB_IN_USE_BY_APPLICATION = 2
    USB_IN_USE_BY_OTHER = 3
    ETH_AVAILABLE = 4
    ETH_IN_USE_BY_APPLICATION = 5
    ETH_IN_USE_BY_OTHER = 6
    ETH_ALREADY_IN_USE_USB = 7


class InterfaceType(IntEnum):
    """InterfaceType enum."""
    RS232 = 0
    USB5216 = 1
    USBMINI = 2
    USB7010 = 3
    ETH7010 = 4


class SensType(IntEnum):
    """SensType enum."""
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


class AvsIdentityType(Structure):
    """IdentityType Structure."""
    _pack_ = 1
    _fields_ = [
        ('SerialNumber', c_char * AVS_SERIAL_LEN),
        ('UserFriendlyName', c_char * USER_ID_LEN),
        ('Status', c_ubyte)
    ]


class BroadcastAnswerType(Structure):
    """BroadcastAnswerType Structure."""
    _pack_ = 1
    _fields_ = [
        ('InterfaceType', c_ubyte),
        ('serial', c_ubyte * AVS_SERIAL_LEN),
        ('port', c_uint16),
        ('status', c_ubyte),
        ('RemoteHostIp', c_uint32),
        ('LocalIp', c_uint32),
        ('reserved', c_ubyte * 4)
    ]


class ControlSettingsType(Structure):
    """ControlSettingsType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_StrobeControl', c_uint16),
        ('m_LaserDelay', c_uint32),
        ('m_LaserWidth', c_uint32),
        ('m_LaserWaveLength', c_float),
        ('m_StoreToRam', c_uint16),
    ]


class DarkCorrectionType(Structure):
    """DarkCorrectionType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Enable', c_ubyte),
        ('m_ForgetPercentage', c_ubyte),
    ]


class DetectorType(Structure):
    """DetectorType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_SensorType', c_ubyte),
        ('m_NrPixels', c_uint16),
        ('m_aFit', c_float * NR_WAVELEN_POL_COEF),
        ('m_NLEnable', c_bool),
        ('m_aNLCorrect', c_double * NR_NONLIN_POL_COEF),
        ('m_aLowNLCounts', c_double),
        ('m_aHighNLCounts', c_double),
        ('m_Gain', c_float * MAX_VIDEO_CHANNELS),
        ('m_Reserved', c_float),
        ('m_Offset', c_float * MAX_VIDEO_CHANNELS),
        ('m_ExtOffset', c_float),
        ('m_DefectivePixels', c_uint16 * NR_DEFECTIVE_PIXELS)
    ]


class SmoothingType(Structure):
    """SmoothingType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_SmoothPix', c_uint16),
        ('m_SmoothModel', c_ubyte),
    ]


class SpectrumCalibrationType(Structure):
    """SpectrumCalibrationType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Smoothing', SmoothingType),
        ('m_CalInttime', c_float),
        ('m_aCalibConvers', c_float * MAX_NR_PIXELS),
    ]


class IrradianceType(Structure):
    """IrradianceType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_IntensityCalib', SpectrumCalibrationType),
        ('m_CalibrationType', c_ubyte),
        ('m_FiberDiameter', c_uint32),
    ]


class SpectrumCorrectionType(Structure):
    """SpectrumCorrectionType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_aSpectrumCorrect', c_float * MAX_NR_PIXELS),
    ]


class TriggerType(Structure):
    """TriggerType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Mode', c_ubyte),
        ('m_Source', c_ubyte),
        ('m_SourceType', c_ubyte),
    ]


class MeasConfigType(Structure):
    """MeasConfigType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_StartPixel', c_uint16),
        ('m_StopPixel', c_uint16),
        ('m_IntegrationTime', c_float),
        ('m_IntegrationDelay', c_uint32),
        ('m_NrAverages', c_uint32),
        ('m_CorDynDark', DarkCorrectionType),
        ('m_Smoothing', SmoothingType),
        ('m_SaturationDetection', c_ubyte),
        ('m_Trigger', TriggerType),
        ('m_Control', ControlSettingsType)
    ]


class TimeStampType(Structure):
    """TimeStampType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Date', c_uint16),
        ('m_Time', c_uint16),
    ]


class StandAloneType(Structure):
    """StandAloneType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Enable', c_bool),
        ('m_Meas', MeasConfigType),
        ('m_Nmsr', c_int16)
    ]


class DynamicStorageType(Structure):
    """DynamicStorageType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Nmsr', c_int32),
        ('m_Reserved', c_ubyte * 8),
    ]


class TempSensorType(Structure):
    """TempSensorType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_aFit', c_float * NR_TEMP_POL_COEF),
    ]


class TecControlType(Structure):
    """TecControlType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Enable', c_bool),
        ('m_Setpoint', c_float),
        ('m_aFit', c_float * NR_DAC_POL_COEF),
    ]


class ProcessControlType(Structure):
    """ProcessControlType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_AnalogLow', c_float * 2),
        ('m_AnalogHigh', c_float * 2),
        ('m_DigitalLow', c_float * 10),
        ('m_DigitalHigh', c_float * 10),
    ]


class EthernetSettingsType(Structure):
    """EthernetSettingsType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_IpAddr', c_uint32),
        ('m_NetMask', c_uint32),
        ('m_Gateway', c_uint32),
        ('m_DhcpEnabled', c_ubyte),
        ('m_TcpPort', c_uint16),
        ('m_LinkStatus', c_ubyte),
    ]


class OemDataType(Structure):
    """OemDataType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_data', c_ubyte * OEM_DATA_LEN)
    ]


class HeartbeatRespType(Structure):
    """HeartbeatRespType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_BitMatrix', c_uint32),
        ('m_Reserved', c_uint32)
    ]


class DeviceConfigType(Structure):
    """DeviceConfigType Structure."""
    _pack_ = 1
    _fields_ = [
        ('m_Len', c_uint16),
        ('m_ConfigVersion', c_uint16),
        ('m_aUserFriendlyId', c_char * USER_ID_LEN),
        ('m_Detector', DetectorType),
        ('m_Irradiance', IrradianceType),
        ('m_Reflectance', SpectrumCalibrationType),
        ('m_SpectrumCorrect', SpectrumCorrectionType),
        ('m_StandAlone', StandAloneType),
        ('m_DynamicStorage', DynamicStorageType),
        ('m_aTemperature', TempSensorType * MAX_TEMP_SENSORS),
        ('m_TecControl', TecControlType),
        ('m_ProcessControl', ProcessControlType),
        ('m_EthernetSettings', EthernetSettingsType),
        ('m_aReserved', c_ubyte * SETTINGS_RESERVED_LEN),
        ('m_OemData', OemDataType)
    ]


if IS_WINDOWS:
    FUNCTYPE = WINFUNCTYPE
else:
    FUNCTYPE = CFUNCTYPE

MeasureCallback = FUNCTYPE(None, POINTER(c_int32), POINTER(c_int32))
"""Used as a decorator for a callback function when a scan is available."""

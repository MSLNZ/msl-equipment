"""
Load the 32-bit ``OL756SDKActiveXCtrl`` library using :ref:`msl-loadlib-welcome`.
"""
from __future__ import annotations

from ctypes import byref
from ctypes import c_double
from ctypes import c_float
from ctypes import c_long
from ctypes import c_short
from enum import Enum

from msl.loadlib import Server32


class _Error(Enum):
    SYSTEM_BUSY = 'Busy performing a measurement.'
    SYSTEM_NOT_CONNECTED = 'OL756 is not connected.'

    SCAN_ERROR = 'Could not acquire measurement.'
    SCAN_CANCELLED = 'Measurement cancelled.'
    SCAN_FLUXOVERLOAD = 'Measurement flux overloaded.'
    SCAN_SIGNALERROR = 'Signal error for measurement.'
    SCAN_PARAMSNOTSENT = 'Parameters have not been sent down. Need to call send_down_parameters().'
    SCAN_DCFAILED = 'Scan failed because signal acquisition returned multiple errors.'

    PARAM_ERR_WAVE_RANGE = 'Wavelength is outside of the available range.'
    PARAM_ERR_WAVE_INC = 'Ending Wavelength problems.'
    PARAM_ERR_SCAN_MODE = 'Scan modes are not valid.'
    PARAM_ERR_INT_TIME = 'Integration time is out of range.'
    PARAM_ERR_SETTLINGTIME = 'Settling time is out of range.'
    PARAM_ERR_GAIN = 'Gain index is out of range.'
    PARAM_ERR_VOLTAGE = 'Invalid voltage.'
    PARAM_ERR_OVERLOAD = 'PMT Flux over load is set too high.'
    PARAM_ERR_DCMODE = 'DC mode is not correct.'
    PARAM_ERR_DCWAVE = 'Dark current wavelength out of spec.'
    PARAM_ERR_MEASTYPE = 'Incorrect measurement type.'
    PARAM_ERR_ATOD_MODE = 'A/D converter not in correct mode.'
    PARAM_ERR_VAL_INDEX = 'Index is out of range.'

    FLASH_READ_ERROR = 'Could not read from the flash.'

    FILE_IO_BADFORMAT = 'File has an invalid format.'
    FILE_IO_FAILED = 'File either does not exist or cannot be loaded.'


ERROR_CODES = {
    0xFFFF: (_Error.SYSTEM_BUSY, _Error.FLASH_READ_ERROR, _Error.FILE_IO_BADFORMAT),
    0x0000: (_Error.SYSTEM_NOT_CONNECTED, _Error.FILE_IO_FAILED),
    0x0002: (_Error.SCAN_ERROR, _Error.PARAM_ERR_WAVE_RANGE),
    0x0004: (_Error.SCAN_CANCELLED, _Error.PARAM_ERR_WAVE_INC),
    0x0008: (_Error.SCAN_FLUXOVERLOAD, _Error.PARAM_ERR_SCAN_MODE),
    0x0010: (_Error.SCAN_SIGNALERROR, _Error.PARAM_ERR_INT_TIME),
    0x0020: (_Error.SCAN_PARAMSNOTSENT, _Error.PARAM_ERR_SETTLINGTIME),
    0x0040: (_Error.SCAN_DCFAILED, _Error.PARAM_ERR_GAIN),
    0x0080: (_Error.PARAM_ERR_VOLTAGE,),
    0x0100: (_Error.PARAM_ERR_OVERLOAD,),
    0x0200: (_Error.PARAM_ERR_DCMODE,),
    0x0400: (_Error.PARAM_ERR_DCWAVE,),
    0x0800: (_Error.PARAM_ERR_MEASTYPE,),
    0x1000: (_Error.PARAM_ERR_ATOD_MODE,),
    0x2000: (_Error.PARAM_ERR_VAL_INDEX,),
}


class OL756(Server32):

    def __init__(self, host, port, **kwargs):
        """Communicates with the 32-bit ``OL756SDKActiveXCtrl`` library."""
        prog_id = kwargs.pop('prog_id')
        mode = int(kwargs.pop('mode'))
        com_port = int(kwargs.pop('com_port'))

        # avoid 32-bit comtypes attempting to import 64-bit numpy
        Server32.remove_site_packages_64bit()

        super(OL756, self).__init__(prog_id, 'activex', host, port, **kwargs)

        self.mode = self.connect_to_ol756(mode, com_port=com_port)

    @staticmethod
    def _check(ret, error_options):
        if ret == 1:
            # SCAN_OK = 0x0001
            # PARAM_OK = 0x0001
            # FLASH_READ_SUCCESS = 0x0001
            # FILE_IO_SUCCESS = 0x0001
            return

        errors = ERROR_CODES.get(ret)
        if errors is None:
            raise RuntimeError(
                'UNKNOWN_ERR_SDK: A return value of {} is not '
                'defined in the OL756 SDK'.format(ret)
            )

        for err in error_options:
            if err in errors:
                raise RuntimeError('{}: {}'.format(err.name, err.value))

        raise RuntimeError(
            'The error code {} does not correspond '
            'with one of the expected error types: {}'.format(
                ret, ', '.join(e.name for e in error_options))
        )

    def accumulate_signals(self, meas_type):
        """Function needs to be called after a measurement was performed.

        This essentially accumulates the data together until the user is
        ready to average out the data. This function is used in combination
        with :meth:`.reset_averaging` and :meth:`.do_averaging`.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance
            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        """
        ret = self.lib.AccumulateSignals(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE))

    def connect_to_ol756(self, mode, com_port=1):
        """Desired mode to connect to OL756. If attempting to connect in RS232 or
        USB mode, and OL756 is not detected, then a dialog box will appear to prompt
        user to select either to retry, cancel or switch to DEMO.

        Parameters
        ----------
        mode : :class:`int`
            Valid modes are:

            * -1: Disconnect. Call this before quitting the application.
            *  0: RS232
            *  1: USB
            *  2: DEMO mode

        com_port : :class:`int`, optional
            If connecting through RS232 then `port` is the COM port number to use.

        Returns
        -------
        :class:`int`
            The mode that was actually used for the connection.
        """
        return self.lib.ConnectToOl756(mode, com_port)

    def do_averaging(self, meas_type, num_to_average):
        """Function divides the accumulated signal by the number of scans
        performed. It then sets the array containing the data with the
        averaged data. This function is used in combination with
        :meth:`.reset_averaging` and :meth:`.accumulate_signals`.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance
            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        num_to_average : :class:`int`
            The number of scans to average.
        """
        ret = self.lib.DoAveraging(meas_type, num_to_average)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE))

    def do_calculations(self, meas_type):
        """Function needs to be called after each measurement to update the calculations.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance
            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        """
        ret = self.lib.DoCalculations(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE))

    def enable_calibration_file(self, meas_type, enable):
        """Enables or disables the use of a calibration file.

        Use this option to generate calibrated results. To open a standard file
        used to create a calibration, use :meth:`.enable_standard_file` instead.

        The user should call :meth:`.load_calibration_file` first to load
        the calibration file before enabling it.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        enable : :class:`bool`
            Whether to enable or disable the use of a calibration file.
        """
        ret = self.lib.EnableCalibrationFile(meas_type, enable)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE, _Error.FILE_IO_FAILED))

    # def enable_dark_compensation(self):
    #     # EnableDarkCompensation -- not in SDK manual
    #     raise NotImplementedError

    def enable_dark_current(self, enable):
        """Turn the dark current on or off.

        Enable this feature if you want the dark current automatically
        acquired and subtracted before each measurement. If you wish to
        take a dark current manually, see the :meth:`.get_dark_current` function.

        The parameters for the dark current will need to be set using
        :meth:`.set_dark_current_params`.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to turn the dark current on or off.
        """
        ret = self.lib.EnableDarkCurrent(enable)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def enable_pmt_protection_mode(self, enable):
        """Turn the PMT protection routines on or off.

        Enable this feature if you want the PMT to be shielded while traveling
        through high intensity spikes. This feature will make the scan slower
        since the wavelength and filter drive will move asynchronously.

        The PMT is still protected by the hardware. This function prevents
        exposure of the PMT while traveling.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to turn the PMT protection routines on or off.
        """
        ret = self.lib.EnablePMTProtectionMode(enable)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def enable_standard_file(self, meas_type, enable):
        """Function enables standard files to be used.

        To open a calibration file used to create a measurement, use
        :meth:`.enable_calibration_file` instead.

        The user should call :meth:`.load_standard_file` first to load
        the standard file before enabling it.

        Parameters
        ----------
        meas_type : :class:`int`
            The calibration measurement type wanted.

            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        enable : :class:`bool`
            Whether to turn the application of the standard file on or off.
        """
        ret = self.lib.EnableStandardFile(meas_type, enable)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE, _Error.FILE_IO_FAILED))

    def export_config_file(self, file_path):
        """Exports the config file into a OL756 compatible configuration file.

        Not all settings used will be applicable.

        Parameters
        ----------
        file_path : :class:`str`
            A valid path to save the file at.
        """
        ret = self.lib.ExportConfigFile(file_path)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def export_registry(self):
        """Save data out to the Windows registry.

        Make sure that a read was done at some point using
        :meth:`.import_registry`. Does not create a configuration file that can
        be loaded into another computer. For that particular function, call
        :meth:`.export_config_file`.
        """
        ret = self.lib.ExportRegistry()
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def get_adaptive_int_time_index(self, gain_index):
        """Get the adaptive integration time index.

        Parameters
        ----------
        gain_index : :class:`int`
            The index of the gain to use to get the integration time.

            * 0 - 1.0E-5
            * 1 - 1.0E-6
            * 2 - 1.0E-7
            * 3 - 1.0E-8
            * 4 - 1.0E-9
            * 5 - 1.0E-10
            * 6 - 1.0E-11

        Returns
        -------
        :class:`int`
            The adaptive integration time index.
        """
        ret = self.lib.GetAdaptiveIntTimeIndex(gain_index)
        if ret == -1:
            raise ValueError('Invalid gain index.')
        return ret

    def get_cri(self, meas_type, index):
        """Get the color-rendering information.

        The user should call :meth:`.do_calculations` at least once before
        calling this function.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance
            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        index : :class:`int`
            The color-rendering index.

            * 0 - General CRI
            * 1 - Light Greyish Red (CRI#1)
            * 2 - Dark Greyish Yellow (CRI#2)
            * 3 - Strong Yellow Green (CRI#3)
            * 4 - Moderate Yellowish Green (CRI#4)
            * 5 - Light Bluish Green (CRI#5)
            * 6 - Light Blue (CRI#6)
            * 7 - Light Violet (CRI#7)
            * 8 - Light Reddish Purple (CRI#8)
            * 9 - Strong Red (CRI#9)
            * 10 - Strong Yellow (CRI#10)
            * 11 - Strong Green (CRI#11)
            * 12 - Strong Blue (CRI#12)
            * 13 - Light Yellowish Pink (CRI#13)
            * 14 - Moderate Olive Green (CRI#14)

        Returns
        -------
        :class:`float`
            The color-rendering information.
        """
        data = c_double()
        ret = self.lib.GetCRI(meas_type, index, byref(data))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE, _Error.PARAM_ERR_VAL_INDEX))
        return data.value

    def get_cal_array(self):
        """This method allows user to get the spectral data of a calibration
        after it is made. The data allows the user to take the data and
        create their own data files.

        Returns
        -------
        :class:`int`
            A pointer to an array of signals.
        :class:`int`
            The number of points acquired.
        """
        num_points = c_long()
        pointer = self.lib.GetCalArray(byref(num_points))
        return pointer, num_points.value

    def get_cal_file_enabled(self, meas_type):
        """Checks to see if the calibration file is enabled.

        The user should call :meth:`.load_calibration_file` first to load the
        calibration file before enabling it.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        Returns
        -------
        :class:`bool`
            Whether the calibration file is enabled.
        """
        if meas_type not in [0, 1, 2]:
            raise ValueError('Invalid measurement type {}. Must be 0, 1 or 2'.format(meas_type))
        return bool(self.lib.GetCalFileEnabled(meas_type))

    def get_calculated_data(self, meas_type, index):
        """Gets data calculated from the intensities.

        The user should call :meth:`.do_calculations` at least once before
        calling this function.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance
            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        index : :class:`int`
            The index to retrieve data of.

            * 0 - Color Temperature
            * 1 - Dominant Wavelength
            * 2 - LED Half Bandwidth
            * 3 - Left Half Bandwidth
            * 4 - Right Half Bandwidth
            * 5 - Peak Spectral Value
            * 6 - LEDPeakWavelength
            * 7 - Radiometric Value
            * 8 - Purity
            * 9 - Center Wavelength
            * 10 - Photometric Value

        Returns
        -------
        :class:`float`
            Pointer to a double to hold the data.
        """
        data = c_double()
        ret = self.lib.GetCalculatedData(meas_type, index, byref(data))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE, _Error.PARAM_ERR_VAL_INDEX))
        return data.value

    def get_calibration_file(self, meas_type):
        """Get a calibration file that is loaded.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        Returns
        -------
        :class:`str`
            String containing the name and path of the calibration file
            that is loaded for a particular measurement type.
        """
        if meas_type not in [0, 1, 2]:
            raise ValueError('Invalid measurement type {}. Must be 0, 1 or 2'.format(meas_type))
        return self.lib.GetCalibrationFile(meas_type)

    def get_chromaticity_data(self, meas_type, index):
        """Get the calculated chromaticity values requested.

        Must have called :meth:`.do_calculations` at least once.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance
            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        index : :class:`int`
            The chromaticity index value [0..70]. See the SDK manual for more details.

        Returns
        -------
        :class:`float`
            Pointer to a double to hold the data.
        """
        data = c_double()
        ret = self.lib.GetChromaticityData(meas_type, index, byref(data))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE, _Error.PARAM_ERR_VAL_INDEX))
        return data.value

    # def get_dc_adj_raw_sig_variant_array(self):
    #     # GetDCAdjRawSigVariantArray -- not in SDK manual
    #     raise NotImplementedError
    
    # def get_dc_adjusted_raw_signal_array(self):
    #     # GetDCAdjustedRawSignalArray -- not in SDK manual
    #     raise NotImplementedError
    
    # def get_dark_compensation_enable(self):
    #     # GetDarkCompensationEnable -- not in SDK manual
    #     raise NotImplementedError
    
    def get_dark_current(self, use_compensation):
        """Takes a manual dark current.

        User will have to subtract from data array by retrieving this array via
        a :meth:`.get_cal_array` or :meth:`.get_signal_array`. This is a special
        function and most users will want to use :meth:`.enable_dark_current`
        instead because it automatically does the subtraction.

        Function if called externally by user program will not have result
        saved out to data file. If the :meth:`.enable_dark_current` was enabled,
        then this function need should not be called.

        Parameters
        ----------
        use_compensation : :class:`int`
            Adjusts dark current for more dynamic ranging using reverse current.

        Returns
        -------
        :class:`float`
            The dark current.
        """
        dark_current = c_double()
        ret = self.lib.GetDarkCurrent(byref(dark_current), use_compensation)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SCAN_PARAMSNOTSENT, _Error.SCAN_DCFAILED))
        return dark_current.value

    def get_dark_current_enable(self):
        """Returns whether the dark-current mode is enabled.

        Returns
        -------
        :class:`bool`
            Whether the dark-current mode is enabled or disabled.
        """
        return bool(self.lib.GetDarkCurrentEnable())

    def get_dark_current_mode(self):
        """Returns whether the dark current is taken at a wavelength or in shutter mode.

        Returns
        -------
        :class:`int`
            The dark-current mode

            * 0 - Dark current in wavelength mode (taken at a particular wavelength designated by the user).
            * 1 - Dark current in shutter mode

        """
        return self.lib.GetDarkCurrentMode()

    def get_dark_current_wavelength(self):
        """Get the dark current wavelength.

        Returns
        -------
        :class:`float`
            Wavelength that the dark current will be taken at.
        """
        return self.lib.GetDarkCurrentWavelength()

    def get_ending_wavelength(self):
        """Get the ending wavelength of the scan range.

        Returns
        -------
        :class:`float`
            The ending wavelength, in nanometers, of the scan range.
        """
        return self.lib.GetEndingWavelength()

    def get_gain_index(self):
        """Get the index of the gain that will be applied when
        the parameters are to be sent down.

        Applies to both quick scan and point to point scans.

        Returns
        -------
        :class:`int`
            The gain index.

            * 0 - 1.0E-5
            * 1 - 1.0E-6
            * 2 - 1.0E-7
            * 3 - 1.0E-8
            * 4 - 1.0E-9
            * 5 - 1.0E-10 (Point to Point mode only)
            * 6 - 1.0E-11 (Point to Point mode only)
            * 7 - Auto Gain Ranging (Point to Point mode only)

        """
        return self.lib.GetGainIndex()

    def get_increment(self):
        """Get the wavelength increment that is used for a scan.

        Returns
        -------
        :class:`float`
            The wavelength increment, in nanometers.
        """
        return self.lib.GetIncrement()

    def get_increment_index(self):
        """Get the index of the wavelength increment that is used for a scan.

        Applies to both quick scan and point to point scans.

        Returns
        -------
        :class:`int`
            Index of the wavelength increment of a scan.

            * 0 - 0.025 nm
            * 1 - 0.05 nm
            * 2 - 0.1 nm
            * 3 - 0.2 nm
            * 4 - 0.5 nm
            * 5 - 1.0 nm
            * 6 - 2.0 nm
            * 7 - 5.0 nm
            * 8 - 10.0 nm

        """
        index = self.lib.GetIncrementIndex()
        return index

    def get_integration_time_index(self, scan_mode):
        """Get the index into the integration time array.

        Applies to both quick scan and point to point scans. In quick scan,
        the speed will vary based on the scan range and increments.

        Parameters
        ----------
        scan_mode : :class:`int`
            The scan mode to use to get the index of.

        Returns
        -------
        :class:`int`
            Point to Point mode

            * 0 - 1.000 sec
            * 1 - 0.500 sec
            * 2 - 0.200 sec
            * 3 - 0.100 sec
            * 4 - 0.050 sec
            * 5 - 0.020 sec
            * 6 - 0.010 sec
            * 7 - 0.005 sec
            * 8 - 0.002 sec
            * 9 - 0.001 sec
            * 10 - Adaptive	(Point To Point mode only)

            Quick Scan mode

            * 0 - slowest
            * 10 - fastest

        """
        if scan_mode not in [0, 1]:
            raise ValueError('Invalid scan mode {}. Must be 0 or 1'.format(scan_mode))
        return self.lib.GetIntegrationTimeIndex(scan_mode)

    def get_ocx_version(self):
        """Get the version of the OL756 SDK ActiveX control.

        Returns
        -------
        :class:`str`
            The software version.
        """
        return self.lib.GetOCXVersion()
    
    def get_pmt_flux_overload(self):
        """Get the voltage of the photomultiplier tube flux overload.

        Returns
        -------
        :class:`float`
            Voltage that the PMT will determine to be at the overload point.
        """
        return self.lib.GetPMTFluxOverload()

    # def get_pmt_protection_mode(self):
    #     # GetPMTProtectionMode -- not in SDK manual
    #     raise NotImplementedError
    
    # def get_pmt_settling_time(self):
    #     # GetPmtSettlingTime -- not in SDK manual
    #     raise NotImplementedError
    
    def get_pmt_voltage(self):
        """Returns the voltage that will sent or has been sent down to the PMT.

        Returns
        -------
        :class:`float`
            Voltage value, in volts, of the photomultiplier tube.
        """
        return self.lib.GetPmtVoltage()

    def get_quick_scan_rate(self):
        """Returns the rate at the quick scan index.

        Returns
        -------
        :class:`float`
            Rate of the quick scan at the current index in nm/s.
        """
        return self.lib.GetQuickScanRate()

    def get_quick_scan_rate_index(self):
        """Returns the index of the quick scan rate.

        Returns
        -------
        :class:`int`
            Index of the quick scan rate.
        """
        return self.lib.GetQuickScanRateIndex()

    # def get_raw_signal_array(self):
    #     # GetRawSignalArray -- not in SDK manual
    #     raise NotImplementedError

    # def get_raw_signal_variant_array(self):
    #     # GetRawSignalVariantArray -- not in SDK manual
    #     raise NotImplementedError
    
    def get_scan_mode(self):
        """Get the mode the scan will be done in.

        Returns
        -------
        :class:`int`
            The scan mode

            * 0 - Point to Point mode
            * 1 - Quick Scan mode

        """
        return self.lib.GetScanMode()

    def get_settling_time(self):
        """Gte the settling time.

        Settling time is time where the wavelength drive pauses once
        it reaches its target wavelength.

        Returns
        -------
        :class:`float`
            Settling time, in seconds, to be sent down or has already been
            sent to the system.
        """
        return self.lib.GetSettlingTime()

    def get_signal_array(self):
        """Get the spectral data of a measurement after it is made.

        Returns
        -------
        :class:`tuple`
            The spectral data.
        """
        num_points = c_long()
        array = self.lib.GetSignalVariantArray(byref(num_points))
        if len(array) != num_points.value:
            raise RuntimeError('Length of the array does not equal the number of points')
        return array

    def get_standard_file(self, meas_type):
        """Retrieves the name of standard file.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type wanted.

            * 3 - Irradiance calibration
            * 4 - Radiance calibration
            * 5 - Transmittance calibration

        Returns
        -------
        :class:`str`
            String containing the name and path of the standard file that is
            loaded for a particular calibration type.
        """
        if meas_type not in [3, 4, 5]:
            raise ValueError('Invalid measurement type {}. Must be 3, 4 or 5'.format(meas_type))
        return self.lib.GetStandardFile(meas_type)

    def get_start_wavelength(self):
        """Get the starting wavelength of a scan.

        Applies to both quick scan and point to point scans.

        Returns
        -------
        :class:`float`
            The wavelength, in nanometers, that the scan will start from.
        """
        return self.lib.GetStartWavelength()

    def get_std_file_enabled(self, meas_type):
        """Checks to see if the standard file is enabled.

        The user should call :meth:`.load_standard_file` first to load
        the standard file before enabling it.

        Parameters
        ----------
        meas_type : :class:`int`
            The calibration type wanted.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        Returns
        -------
        :class:`bool`
            Whether a standard file is enabled.
        """
        if meas_type not in [0, 1, 2]:
            raise ValueError('Invalid measurement type {}. Must be 0, 1 or 2'.format(meas_type))
        return bool(self.lib.GetStdFileEnabled(meas_type))

    def import_config_file(self, path):
        """The file is a standard OL756 configuration file.

        Not all settings used will be applicable. Measurement type is not used
        because in the SDK, the :meth:`.take_point_to_point_measurement`
        function has as an input the measurement type. The user should select
        the type and not have it based on the configuration file.

        Parameters
        ----------
        path : :class:`str`
            A valid path to load the file at.
        """
        ret = self.lib.ImportConfigFile(path)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def import_registry(self):
        """Loads data from the registry.

        Loads default if no registry exists. To import the configuration
        from another computer, use :meth:`.import_config_file` instead.

        Not all settings used will be applicable. Measurement type is not
        used because in the SDK, the :meth:`.take_point_to_point_measurement`
        function has as an input the measurement type. The user should
        select the type and not have it based on the configuration file.
        """
        ret = self.lib.ImportRegistry()
        self._check(ret, (_Error.SYSTEM_BUSY,))

    # def init_sdk(self):
    #     # InitSDK -- not in the SDK manual
    #     raise NotImplementedError
    
    def load_calibration_file(self, path, meas_type):
        """Load a calibration file.

        Parameters
        ----------
        path : :class:`str`
            The path of a calibration file.
        meas_type : :class:`int`
            The measurement type.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        """
        if meas_type not in [0, 1, 2]:
            raise ValueError('Invalid measurement type {}. Must be 0, 1 or 2'.format(meas_type))
        ret = self.lib.LoadCalibrationFile(path, meas_type)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def load_standard_file(self, path, meas_type):
        """Load a standard file.

        Parameters
        ----------
        path : :class:`str`
            The path of a standard file.
        meas_type : :class:`int`
            The measurement type.

            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        """
        if meas_type not in [3, 4, 5]:
            raise ValueError('Invalid measurement type {}. Must be 3, 4 or 5'.format(meas_type))
        ret = self.lib.LoadStandardFile(path, meas_type)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def manual_filter_drive_connect(self, connect):
        """Used to connect or disconnect the filter drive.

        Disconnecting essentially acquires scans without the filter.

        Parameters
        ----------
        connect : :class:`bool`
            Connect or disconnect the filter drive. Reconnecting will
            home the wavelength and filter drive.
        """
        ret = self.lib.ManualFilterDriveConnect(connect)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED))

    def manual_get_gain(self):
        """The index of the gain that will be applied when the parameters are to be sent down.

        Returns
        -------
        :class:`int`
            The gain index.

            * 0 - 1.0E-5
            * 1 - 1.0E-6
            * 2 - 1.0E-7
            * 3 - 1.0E-8
            * 4 - 1.0E-9
            * 5 - 1.0E-10 (Point to Point mode only)
            * 6 - 1.0E-11 (Point to Point mode only)
            * 7 - Auto Gain Ranging (Point to Point mode only)

        """
        gain_index = c_short()
        mode = c_short()
        ret = self.lib.ManualGetGain(byref(gain_index), byref(mode))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return gain_index.value

    def manual_get_integration_time(self):
        """Returns the integration time set in the system.

        Only applies to the integration time used for Point to Point scans.

        Returns
        -------
        :class:`float`
            The integration time in seconds.
        """
        int_time = c_float()
        ret = self.lib.ManualGetIntegrationTime(byref(int_time))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return int_time.value

    def manual_get_pmt_overload(self):
        """Returns the PMT overload voltage set in the system.

        Returns
        -------
        :class:`float`
            Overload voltage, in volts, of the photomultiplier tube.
        """
        overload = c_double()
        ret = self.lib.ManualGetPMTOverload(byref(overload))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return overload.value

    def manual_get_pmt_voltage(self):
        """Returns the PMT high voltage set in the system.

        Returns
        -------
        :class:`float`
            Voltage, in volts, of the photomultiplier tube.
        """
        pmt_voltage = c_double()
        ret = self.lib.ManualGetPMTVoltage(byref(pmt_voltage))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return pmt_voltage.value

    def manual_get_settling_time(self):
        """Returns the settling time of the instrument.

        Returns
        -------
        :class:`float`
            Settling time of the system in seconds.
        """
        settling_time = c_float()
        ret = self.lib.ManualGetSettlingTime(byref(settling_time))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return settling_time.value

    def manual_get_signal(self):
        """Returns the signal at the current position of the wavelength drive.

        Returns
        -------
        :class:`float`
            The signal, in amperes.
        """
        signal = c_double()
        ret = self.lib.ManualGetSignal(byref(signal))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return signal.value

    def manual_home_ol756(self):
        """Homes the wavelength and filter drive.

        Will reconnect the filter drive if it was disconnected
        """
        ret = self.lib.ManualHomeOL756()
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def manual_move_to_wavelength(self, wavelength):
        """Moves the wavelength drive to a particular location.

        Parameters
        ----------
        wavelength : :class:`float`
            The wavelength to move the wavelength drive to.
        """
        ret = self.lib.ManualMoveToWavelength(wavelength)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED,
                          _Error.PARAM_ERR_WAVE_RANGE, _Error.PARAM_ERR_ATOD_MODE))

    def manual_set_gain(self, gain_index, mode):
        """Set the gain.

        Parameters
        ----------
        gain_index : :class:`int`
            The gain index.

            * 0 - 1.0E-5
            * 1 - 1.0E-6
            * 2 - 1.0E-7
            * 3 - 1.0E-8
            * 4 - 1.0E-9
            * 5 - 1.0E-10 (Point to Point mode only)
            * 6 - 1.0E-11 (Point to Point mode only)
            * 7 - Auto Gain Ranging (Point to Point mode only)

        mode : :class:`int`
            The scan mode

            * 0 - point to point
            * 1 - quick scan
        """
        ret = self.lib.ManualSetGain(gain_index, mode)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED,
                          _Error.PARAM_ERR_ATOD_MODE, _Error.PARAM_ERR_SCAN_MODE,
                          _Error.PARAM_ERR_GAIN))

    def manual_set_integration_time(self, time):
        """Sets the integration time set in the system.

        Only applies to the integration time used for Point to Point scans.

        Parameters
        ----------
        time : :class:`float`
            The integration time in seconds.
        """
        ret = self.lib.ManualSetIntegrationTime(time)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def manual_set_pmt_overload(self, overload):
        """Sets the PMT overload voltage set in the system.

        Parameters
        ----------
        overload : :class:`float`
            Overload voltage, in volts, of the photomultiplier tube in Volts.
        """
        ret = self.lib.ManualSetPMTOverload(overload)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def manual_set_pmt_voltage(self, voltage):
        """Sets the PMT high voltage set in the system.

        Parameters
        ----------
        voltage : :class:`float`
            Voltage, in volts, of the photomultiplier tube.
        """
        ret = self.lib.ManualSetPMTVoltage(voltage)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def manual_set_settling_time(self, time):
        """Sets the settling time of the instrument.

        Parameters
        ----------
        time : :class:`float`
            Settling time of the system.
        """
        ret = self.lib.ManualSetSettlingTime(time)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def move_to_wavelength(self, wavelength):
        """Moves the wavelength drive to a particular location.

        Parameters
        ----------
        wavelength : :class:`float`
            The wavelength, in nanometers, to move the wavelength drive to.
        """
        ret = self.lib.MoveToWavelength(wavelength)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_WAVE_RANGE))

    def read_ol756_flash_settings(self):
        """Reads the saved settings from the flash memory.

        Reads the settings such as the grating alignment factor, filter skew
        and wavelength skew. Loads these values into the ActiveX control memory.
        """
        ret = self.lib.ReadOL756FlashSettings()
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.FLASH_READ_ERROR))

    def reset_averaging(self, meas_type):
        """Resets the accumulated signal array for the specified measurement type.

        This function is used in combination with :meth:`.do_averaging`
        and :meth:`.accumulate_signals`.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance
            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        """
        ret = self.lib.ResetAveraging(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEASTYPE))

    def save_calibration_file(self, meas_type, path):
        """Create a OL756-compatible calibration file.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type.

            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        path : :class:`str`
            The path to save the calibration file to.
        """
        if meas_type not in [3, 4, 5]:
            raise ValueError('Invalid measurement type {}. Must be 3, 4 or 5'.format(meas_type))
        ret = self.lib.SaveCalibrationFile(meas_type, path)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def save_measurement_data(self, meas_type, path):
        """Save the measurement data to a OL756-compatible data file.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        path : :class:`str`
            The path to save the data to.
        """
        if meas_type not in [0, 1, 2]:
            raise ValueError('Invalid measurement type {}. Must be 0, 1 or 2'.format(meas_type))
        self.lib.SaveMeasurementData(meas_type, path)
        # FILE_IO_FAILED was raised even if the file was successfully created
        # self._check(ret, (_Error.FILE_IO_FAILED,))

    def send_down_parameters(self, scan_mode):
        """Sends down the parameters to the system.

        This needs to be called whenever parameters dealing with the PMT or
        integration time and gain has changed. Needs to be called once before
        doing any measurements or other signal acquisition including dark
        current.

        The following methods affect the parameters:
        :meth:`.set_pmt_flux_overload_voltage`
        :meth:`.set_gain`
        :meth:`.set_integration_time`
        :meth:`.set_pmt_hi_voltage`
        :meth:`.set_settling_time`
        :meth:`.set_scan_range`
        :meth:`.set_adaptive_integration_time`

        Parameters
        ----------
        scan_mode : :class:`int`
            The scan mode.

            * 0 - Point to point
            * 1 - Quick scan

        """
        if scan_mode not in [0, 1]:
            raise ValueError('Invalid scan mode {}. Must be 0 or 1'.format(scan_mode))
        ret = self.lib.SendDownParameters(scan_mode)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def set_adaptive_integration_time(self, gain_index, speed_index):
        """Sets the scan speed of the scan at a particular gain range.

        Adaptive integration time is used solely for point to point
        scans in auto-gain ranging.

        Parameters
        ----------
        gain_index : :class:`int`
            The index of the gain to use to set the integration time.

            * 0 - 1.0E-5
            * 1 - 1.0E-6
            * 2 - 1.0E-7
            * 3 - 1.0E-8
            * 4 - 1.0E-9
            * 5 - 1.0E-10
            * 6 - 1.0E-11

        speed_index : :class:`int`
            The scan speed index [0..12] -- 0=Slowest, 12=Fastest.
        """
        ret = self.lib.SetAdaptiveIntegrationTime(gain_index, speed_index)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_GAIN, _Error.PARAM_ERR_INT_TIME))

    def set_averaging_number_of_scan(self, num_avg_scans):
        """Set the number of scans to average.

        Parameters
        ----------
        num_avg_scans : :class:`int`
            The number of scans to average.
        """
        ret = self.lib.SetAveragingNumberOfScan(num_avg_scans)
        # this function is not in the SDK manual
        # so not sure what error codes it can return
        self._check(ret, ())

    def set_dark_current_params(self, mode, wavelength):
        """Sets the mode and the wavelength to use for a dark-current measurement.

        Parameters
        ----------
        mode : :class:`int`
            The mode to use to acquire a dark-current measurement

            * 0 - wavelength
            * 1 - shutter

        wavelength : :class:`float`
            The wavelength, in nanometers, to use for a dark-current measurement.
        """
        ret = self.lib.SetDarkCurrentParams(mode, wavelength)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_DCMODE, _Error.PARAM_ERR_DCWAVE))

    def set_gain(self, scan_mode, gain_index):
        """Sets the index of the gain that will be applied
        when the parameters are to be sent down.

        Applies to both quick scan and point to point scans.

        Parameters
        ----------
        scan_mode : :class:`int`
            The scan mode

            * 0 - Point to Point
            * 1 - Quick Scan

        gain_index : :class:`int`
            The gain index

            * 0 - 1.0E-5
            * 1 - 1.0E-6
            * 2 - 1.0E-7
            * 3 - 1.0E-8
            * 4 - 1.0E-9
            * 5 - 1.0E-10 (available only in Point to Point mode)
            * 6 - 1.0E-11 (available only in Point to Point mode)
            * 7 - Auto Gain Ranging (available only in Point to Point mode)

        """
        ret = self.lib.SetGain(scan_mode, gain_index)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_GAIN, _Error.PARAM_ERR_SCAN_MODE))

    def set_integration_time(self, scan_mode, scan_speed):
        """Sets the index of the scan speed used.

        Applies to both quick scan and point to point scans.
        In quick scan, the speed will vary based on the scan range and increments.

        Parameters
        ----------
        scan_mode : :class:`int`
            The scan mode

            * 0 - Point to Point
            * 1 - Quick Scan

        scan_speed : :class:`int`
            Index to the integration time array

            Point to Point mode

                * 0 - 1.000 sec
                * 1 - 0.500 sec
                * 2 - 0.200 sec
                * 3 - 0.100 sec
                * 4 - 0.050 sec
                * 5 - 0.020 sec
                * 6 - 0.010 sec
                * 7 - 0.005 sec
                * 8 - 0.002 sec
                * 9 - 0.001 sec
                * 10 - Adaptive	(Point To Point mode only)
                * 11 - User defined (Point To Point mode only)

            Quick Scan mode

                * 0 - slowest
                * 10 - fastest

        """
        ret = self.lib.SetIntegrationTime(scan_mode, scan_speed)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_SCAN_MODE, _Error.PARAM_ERR_INT_TIME))

    def set_pmt_flux_overload_voltage(self, overload_voltage):
        """Sets the value to use for the photomultiplier tube flux overload.

        Parameters
        ----------
        overload_voltage : :class:`float`
            Voltage that the PMT will determine to be at the overload point.
            Software only, because PMT has built-in protection also.
        """
        ret = self.lib.SetPMTFluxOverloadVoltage(overload_voltage)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_OVERLOAD))

    def set_pmt_hi_voltage(self, hi_voltage):
        """Sets the value to be determined to be a flux overload by the software.

        Parameters
        ----------
        hi_voltage : :class:`float`
            Voltage, in volts, that the PMT will determine to be overload point.
        """
        ret = self.lib.SetPMTHiVoltage(hi_voltage)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_OVERLOAD))

    # def set_pmt_settling_time(self, time):
    #     """Set the settling time of the photomultiplier tube.
    #
    #     Not in the SDK manual.
    #
    #     Parameters
    #     ----------
    #     time : :class:`int`
    #         Settling Time in seconds.
    #     """
    #     ret = self.lib.SetPmtSettlingTime(time)
    #     self._check(ret, ())

    def set_reference_white_point(self, white, user_def_x, user_def_y):
        """Sets the value of the reference illuminant.

        Parameters
        ----------
        white : :class:`int`
            The reference white point

            * 0 - Incandescent(A)
            * 1 - Direct Sunlight(B)
            * 2 - Indirect Sunlight(C)
            * 3 - Natural Daylight(D65)
            * 4 - Normalized Reference(E)
            * 5 - User Defined

        user_def_x : :class:`float`
            User defined x on CIE chart.
        user_def_y : :class:`float`
            User defined y on CIE chart.
        """
        ret = self.lib.SetReferenceWhitePoint(white, user_def_x, user_def_y)
        self._check(ret, ())

    def set_scan_range(self, start, end, inc_index):
        """Sets the wavelength scan range.

        Parameters
        ----------
        start : :class:`float`
            Starting wavelength, in nanometers.
        end : :class:`float`
            Ending wavelength, in nanometers.
        inc_index : :class:`int`
            Increment index, in nanometers.
        """
        ret = self.lib.SetScanRange(start, end, inc_index)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_WAVE_RANGE, _Error.PARAM_ERR_WAVE_INC))

    def set_settling_time(self, time):
        """Set the settling time.

        Settling time is the time that the wavelength drive pauses once
        it reaches its target wavelength.

        Parameters
        ----------
        time : :class:`float`
            Settling Time in seconds to be sent down or has already
            been sent to the system.
        """
        ret = self.lib.SetSettlingTime(time)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def set_tab_delimited_mode(self, enable):
        """Purpose of function is to set what mode to write the data files as.

        Setting the tab delimited to true will write the data in a tab
        delimited format, else a false will write in a comma delimited format.
        Tab delimited files will not be compatible with some versions of the
        software. If you want data files to be compatible with v1.32 software
        and below, leave the mode to :data:`False`.

        Parameters
        ----------
        enable : :class:`bool`
            Whether to use the new file format using TABs as a delimited or
            the old file format compatible with v1.32 and below.
        """
        self.lib.SetTabDelimitedMode(enable)

    def set_user_defined_integration_time(self, time):
        """Sets the user defined integration time to be used only in point to
        point scans and only if the user sets the integration time mode.

        Parameters
        ----------
        time : :class:`float`
            Integration time in seconds.
        """
        ret = self.lib.SetUserDefinedIntegrationTime(time)
        self._check(ret, (_Error.PARAM_ERR_INT_TIME,))

    def stop_measurement(self):
        """Stops a measurement.

        Applies only to Point to Point measurements. Quick scans are done
        so quickly that there is no need to stop a measurement once it starts.
        """
        ret = self.lib.StopMeasurement()
        self._check(ret, ())

    def take_point_to_point_calibration(self, meas_type):
        """Takes a calibration in point to point mode.

        Need to have called :meth:`.send_down_parameters` at least once before
        calling any of the measurement functions or data acquisition functions.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type.

            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        """
        ret = self.lib.TakePointToPointCalibration(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED,
                          _Error.SCAN_PARAMSNOTSENT, _Error.SCAN_CANCELLED,
                          _Error.SCAN_FLUXOVERLOAD, _Error.PARAM_ERR_MEASTYPE))

    def take_point_to_point_measurement(self, meas_type):
        """Takes a measurement in point to point mode.

        Need to have called :meth:`.send_down_parameters` at least once before
        calling any of the measurement functions or data acquisition functions.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        """
        ret = self.lib.TakePointToPointMeasurement(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED,
                          _Error.SCAN_PARAMSNOTSENT, _Error.SCAN_CANCELLED,
                          _Error.SCAN_FLUXOVERLOAD, _Error.PARAM_ERR_MEASTYPE))

    def take_quick_scan_calibration(self, meas_type):
        """Takes a calibration in quick scan mode.

        Need to have called :meth:`.send_down_parameters` at least once before
        calling any of the measurement functions or data acquisition functions.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type.

            * 3 - Irradiance Calibration
            * 4 - Radiance Calibration
            * 5 - Transmittance Calibration

        """
        if meas_type not in [3, 4, 5]:
            raise ValueError('Invalid measurement type {}. Must be 3, 4 or 5'.format(meas_type))
        ret = self.lib.TakeQuickScanCalibration(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.SCAN_PARAMSNOTSENT))

    def take_quick_scan_measurement(self, meas_type):
        """Takes a measurement in quick scan mode.

        Need to have called :meth:`.send_down_parameters` at least once before
        calling any of the measurement functions or data acquisition functions.

        Parameters
        ----------
        meas_type : :class:`int`
            The measurement type.

            * 0 - Irradiance
            * 1 - Radiance
            * 2 - Transmittance

        """
        if meas_type not in [0, 1, 2]:
            raise ValueError('Invalid measurement type {}. Must be 0, 1 or 2'.format(meas_type))
        ret = self.lib.TakeQuickScanMeasurement(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.SCAN_PARAMSNOTSENT))

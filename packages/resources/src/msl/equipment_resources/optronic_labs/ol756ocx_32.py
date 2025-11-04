"""Load the 32-bit `OL756SDKActiveXCtrl` library."""

# cSpell: ignore ATOD
from __future__ import annotations

from ctypes import byref, c_double, c_float, c_int32, c_long, c_short
from enum import Enum

from msl.loadlib import Server32


class _Error(Enum):
    SYSTEM_BUSY = "Busy performing a measurement."
    SYSTEM_NOT_CONNECTED = "OL756 is not connected."

    SCAN_ERROR = "Could not acquire measurement."
    SCAN_CANCELLED = "Measurement cancelled."
    SCAN_FLUX_OVERLOAD = "Measurement flux overloaded."
    SCAN_SIGNAL_ERROR = "Signal error for measurement."
    SCAN_PARAMS_NOT_SENT = "Parameters have not been sent down. Need to call send_down_parameters()."
    SCAN_DC_FAILED = "Scan failed because signal acquisition returned multiple errors."

    PARAM_ERR_WAVE_RANGE = "Wavelength is outside of the available range."
    PARAM_ERR_WAVE_INC = "Ending Wavelength problems."
    PARAM_ERR_SCAN_MODE = "Scan modes are not valid."
    PARAM_ERR_INT_TIME = "Integration time is out of range."
    PARAM_ERR_SETTLING_TIME = "Settling time is out of range."
    PARAM_ERR_GAIN = "Gain index is out of range."
    PARAM_ERR_VOLTAGE = "Invalid voltage."
    PARAM_ERR_OVERLOAD = "PMT Flux over load is set too high."
    PARAM_ERR_DC_MODE = "DC mode is not correct."
    PARAM_ERR_DC_WAVE = "Dark current wavelength out of spec."
    PARAM_ERR_MEAS_TYPE = "Incorrect measurement type."
    PARAM_ERR_ATOD_MODE = "A/D converter not in correct mode."
    PARAM_ERR_VAL_INDEX = "Index is out of range."

    FLASH_READ_ERROR = "Could not read from the flash."

    FILE_IO_BAD_FORMAT = "File has an invalid format."
    FILE_IO_FAILED = "File either does not exist or cannot be loaded."


ERROR_CODES = {
    0xFFFF: (_Error.SYSTEM_BUSY, _Error.FLASH_READ_ERROR, _Error.FILE_IO_BAD_FORMAT),
    0x0000: (_Error.SYSTEM_NOT_CONNECTED, _Error.FILE_IO_FAILED),
    0x0002: (_Error.SCAN_ERROR, _Error.PARAM_ERR_WAVE_RANGE),
    0x0004: (_Error.SCAN_CANCELLED, _Error.PARAM_ERR_WAVE_INC),
    0x0008: (_Error.SCAN_FLUX_OVERLOAD, _Error.PARAM_ERR_SCAN_MODE),
    0x0010: (_Error.SCAN_SIGNAL_ERROR, _Error.PARAM_ERR_INT_TIME),
    0x0020: (_Error.SCAN_PARAMS_NOT_SENT, _Error.PARAM_ERR_SETTLING_TIME),
    0x0040: (_Error.SCAN_DC_FAILED, _Error.PARAM_ERR_GAIN),
    0x0080: (_Error.PARAM_ERR_VOLTAGE,),
    0x0100: (_Error.PARAM_ERR_OVERLOAD,),
    0x0200: (_Error.PARAM_ERR_DC_MODE,),
    0x0400: (_Error.PARAM_ERR_DC_WAVE,),
    0x0800: (_Error.PARAM_ERR_MEAS_TYPE,),
    0x1000: (_Error.PARAM_ERR_ATOD_MODE,),
    0x2000: (_Error.PARAM_ERR_VAL_INDEX,),
}


class OL756x86(Server32):
    """Load the 32-bit `OL756SDKActiveXCtrl` library."""

    def __init__(self, host: str, port: int, **kwargs: str) -> None:
        """Load the 32-bit `OL756SDKActiveXCtrl` library."""
        prog_id = kwargs.pop("prog_id")
        mode = int(kwargs.pop("mode"))
        com_port = int(kwargs.pop("com_port"))

        # avoid 32-bit comtypes attempting to import 64-bit numpy
        _ = Server32.remove_site_packages_64bit()

        super().__init__(prog_id, "activex", host, port, **kwargs)

        self.mode: int = self._connect_to_ol756(mode, com_port=com_port)

    @staticmethod
    def _check(ret: int, error_options: tuple[_Error, ...]) -> None:
        if ret == 1:  # SCAN_OK, PARAM_OK, FLASH_READ_SUCCESS, FILE_IO_SUCCESS
            return

        errors = ERROR_CODES.get(ret)
        if errors is None:
            msg = f"UnknownError: A return value of {ret} is not defined in the OL756 SDK"
            raise RuntimeError(msg)

        for err in error_options:
            if err in errors:
                msg = f"{err.name}: {err.value}"
                raise RuntimeError(msg)

        names = ", ".join(e.name for e in error_options)
        msg = f"The error code {ret} does not correspond with one of the expected error types: {names}"
        raise RuntimeError(msg)

    def _accumulate_signals(self, meas_type: int) -> None:
        ret = self.lib.AccumulateSignals(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE))

    def _connect_to_ol756(self, mode: int, com_port: int = 1) -> int:
        """Desired mode to connect to OL756.

        If attempting to connect in RS-232 or USB mode, and OL756 is not detected, then a
        dialog box will appear to prompt user to select either to retry, cancel or switch to DEMO.

        Args:
            mode: The connection mode.

                * `-1` &mdash; Disconnect. Call this before quitting the application.
                * `0` &mdash; RS-232
                * `1` &mdash; USB
                * `2` &mdash; DEMO mode

            com_port: If connecting through RS-232, the *COM* port number to use.

        Returns:
            The mode that was actually used for the connection.
        """
        return int(self.lib.ConnectToOl756(mode, com_port))

    def _do_averaging(self, meas_type: int, n_scans: int) -> None:
        ret = self.lib.DoAveraging(meas_type, n_scans)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE))

    def _do_calculations(self, meas_type: int) -> None:
        ret = self.lib.DoCalculations(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE))

    def _enable_calibration_file(self, meas_type: int, enable: bool) -> None:  # noqa: FBT001
        ret = self.lib.EnableCalibrationFile(meas_type, enable)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE, _Error.FILE_IO_FAILED))

    # def enable_dark_compensation(self):
    #     # EnableDarkCompensation -- not in SDK manual
    #     raise NotImplementedError

    def _enable_dark_current(self, enable: bool = True) -> None:  # noqa: FBT001, FBT002
        ret = self.lib.EnableDarkCurrent(enable)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def _enable_pmt_protection_mode(self, enable: bool) -> None:  # noqa: FBT001
        ret = self.lib.EnablePMTProtectionMode(enable)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def _enable_standard_file(self, meas_type: int, enable: bool) -> None:  # noqa: FBT001
        ret = self.lib.EnableStandardFile(meas_type, enable)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE, _Error.FILE_IO_FAILED))

    def _export_config_file(self, file_path: str) -> None:
        ret = self.lib.ExportConfigFile(file_path)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def _export_registry(self) -> None:
        ret = self.lib.ExportRegistry()
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def _get_adaptive_int_time_index(self, gain_index: int) -> int:
        return int(self.lib.GetAdaptiveIntTimeIndex(gain_index))

    def _get_cri(self, meas_type: int, index: int) -> float:
        data = c_double()
        ret = self.lib.GetCRI(meas_type, index, byref(data))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE, _Error.PARAM_ERR_VAL_INDEX))
        return data.value

    def _get_cal_array(self) -> list[int]:
        num_points = c_long()
        pointer = int(self.lib.GetCalArray(byref(num_points)))
        c_array = c_int32 * num_points.value
        array = c_array.from_address(pointer)
        return list(array)

    def _get_cal_file_enabled(self, meas_type: int) -> bool:
        return bool(self.lib.GetCalFileEnabled(meas_type))

    def _get_calculated_data(self, meas_type: int, index: int) -> float:
        data = c_double()
        ret = self.lib.GetCalculatedData(meas_type, index, byref(data))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE, _Error.PARAM_ERR_VAL_INDEX))
        return data.value

    def _get_calibration_file(self, meas_type: int) -> str:
        return str(self.lib.GetCalibrationFile(meas_type))

    def _get_chromaticity_data(self, meas_type: int, index: int) -> float:
        data = c_double()
        ret = self.lib.GetChromaticityData(meas_type, index, byref(data))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE, _Error.PARAM_ERR_VAL_INDEX))
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

    def _get_dark_current(self, use_compensation: int) -> float:
        dark_current = c_double()
        ret = self.lib.GetDarkCurrent(byref(dark_current), use_compensation)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SCAN_PARAMS_NOT_SENT, _Error.SCAN_DC_FAILED))
        return dark_current.value

    def _get_dark_current_enable(self) -> bool:
        return bool(self.lib.GetDarkCurrentEnable())

    def _get_dark_current_mode(self) -> int:
        return int(self.lib.GetDarkCurrentMode())

    def _get_dark_current_wavelength(self) -> float:
        return float(self.lib.GetDarkCurrentWavelength())

    def _get_ending_wavelength(self) -> float:
        return float(self.lib.GetEndingWavelength())

    def _get_gain_index(self) -> int:
        return int(self.lib.GetGainIndex())

    def _get_increment(self) -> float:
        return float(self.lib.GetIncrement())

    def _get_increment_index(self) -> int:
        return int(self.lib.GetIncrementIndex())

    def _get_integration_time_index(self, scan_mode: int) -> int:
        return int(self.lib.GetIntegrationTimeIndex(scan_mode))

    def _get_ocx_version(self) -> str:
        return str(self.lib.GetOCXVersion())

    def _get_pmt_flux_overload(self) -> float:
        return float(self.lib.GetPMTFluxOverload())

    # def get_pmt_protection_mode(self):
    #     # GetPMTProtectionMode -- not in SDK manual
    #     raise NotImplementedError

    # def get_pmt_settling_time(self):
    #     # GetPmtSettlingTime -- not in SDK manual
    #     raise NotImplementedError

    def _get_pmt_voltage(self) -> float:
        return float(self.lib.GetPmtVoltage())

    def _get_quick_scan_rate(self) -> float:
        return float(self.lib.GetQuickScanRate())

    def _get_quick_scan_rate_index(self) -> int:
        return int(self.lib.GetQuickScanRateIndex())

    # def get_raw_signal_array(self):
    #     # GetRawSignalArray -- not in SDK manual
    #     raise NotImplementedError

    # def get_raw_signal_variant_array(self):
    #     # GetRawSignalVariantArray -- not in SDK manual
    #     raise NotImplementedError

    def _get_scan_mode(self) -> int:
        return int(self.lib.GetScanMode())

    def _get_settling_time(self) -> float:
        return float(self.lib.GetSettlingTime())

    def _get_signal_array(self) -> tuple[int, ...]:
        num_points = c_long()
        array: tuple[int, ...] = self.lib.GetSignalVariantArray(byref(num_points))
        if len(array) != num_points.value:
            msg = "Length of the array does not equal the number of points"
            raise RuntimeError(msg)
        return array

    def _get_standard_file(self, meas_type: int) -> str:
        return str(self.lib.GetStandardFile(meas_type))

    def _get_start_wavelength(self) -> float:
        return float(self.lib.GetStartWavelength())

    def _get_std_file_enabled(self, meas_type: int) -> bool:
        return bool(self.lib.GetStdFileEnabled(meas_type))

    def _import_config_file(self, path: str) -> None:
        ret = self.lib.ImportConfigFile(path)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def _import_registry(self) -> None:
        ret = self.lib.ImportRegistry()
        self._check(ret, (_Error.SYSTEM_BUSY,))

    # def init_sdk(self):
    #     # InitSDK -- not in the SDK manual
    #     raise NotImplementedError

    def _load_calibration_file(self, path: str, meas_type: int) -> None:
        ret = self.lib.LoadCalibrationFile(path, meas_type)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def _load_standard_file(self, path: str, meas_type: int) -> None:
        ret = self.lib.LoadStandardFile(path, meas_type)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def _manual_filter_drive_connect(self, connect: bool) -> None:  # noqa: FBT001
        ret = self.lib.ManualFilterDriveConnect(connect)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED))

    def _manual_get_gain(self) -> int:
        gain_index = c_short()
        mode = c_short()
        ret = self.lib.ManualGetGain(byref(gain_index), byref(mode))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return gain_index.value

    def _manual_get_integration_time(self) -> float:
        int_time = c_float()
        ret = self.lib.ManualGetIntegrationTime(byref(int_time))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return int_time.value

    def _manual_get_pmt_overload(self) -> float:
        overload = c_double()
        ret = self.lib.ManualGetPMTOverload(byref(overload))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return overload.value

    def _manual_get_pmt_voltage(self) -> float:
        pmt_voltage = c_double()
        ret = self.lib.ManualGetPMTVoltage(byref(pmt_voltage))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return pmt_voltage.value

    def _manual_get_settling_time(self) -> float:
        settling_time = c_float()
        ret = self.lib.ManualGetSettlingTime(byref(settling_time))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return settling_time.value

    def _manual_get_signal(self) -> float:
        signal = c_double()
        ret = self.lib.ManualGetSignal(byref(signal))
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))
        return signal.value

    def _manual_home_ol756(self) -> None:
        ret = self.lib.ManualHomeOL756()
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def _manual_move_to_wavelength(self, wavelength: float) -> None:
        ret = self.lib.ManualMoveToWavelength(wavelength)
        self._check(
            ret,
            (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_WAVE_RANGE, _Error.PARAM_ERR_ATOD_MODE),
        )

    def _manual_set_gain(self, gain_index: int, mode: int) -> None:
        ret = self.lib.ManualSetGain(gain_index, mode)
        self._check(
            ret,
            (
                _Error.SYSTEM_BUSY,
                _Error.SYSTEM_NOT_CONNECTED,
                _Error.PARAM_ERR_ATOD_MODE,
                _Error.PARAM_ERR_SCAN_MODE,
                _Error.PARAM_ERR_GAIN,
            ),
        )

    def _manual_set_integration_time(self, time: float) -> None:
        ret = self.lib.ManualSetIntegrationTime(time)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def _manual_set_pmt_overload(self, overload: float) -> None:
        ret = self.lib.ManualSetPMTOverload(overload)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def _manual_set_pmt_voltage(self, voltage: float) -> None:
        ret = self.lib.ManualSetPMTVoltage(voltage)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def _manual_set_settling_time(self, time: float) -> None:
        ret = self.lib.ManualSetSettlingTime(time)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.PARAM_ERR_ATOD_MODE))

    def _move_to_wavelength(self, wavelength: float) -> None:
        ret = self.lib.MoveToWavelength(wavelength)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_WAVE_RANGE))

    def _read_ol756_flash_settings(self) -> None:
        ret = self.lib.ReadOL756FlashSettings()
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.FLASH_READ_ERROR))

    def _reset_averaging(self, meas_type: int) -> None:
        ret = self.lib.ResetAveraging(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_MEAS_TYPE))

    def _save_calibration_file(self, meas_type: int, path: str) -> None:
        ret = self.lib.SaveCalibrationFile(meas_type, path)
        self._check(ret, (_Error.FILE_IO_FAILED,))

    def _save_measurement_data(self, meas_type: int, path: str) -> None:
        self.lib.SaveMeasurementData(meas_type, path)
        # FILE_IO_FAILED was raised even if the file was successfully created
        # self._check(ret, (_Error.FILE_IO_FAILED,))  # noqa: ERA001

    def _send_down_parameters(self, scan_mode: int) -> None:
        ret = self.lib.SendDownParameters(scan_mode)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def _set_adaptive_integration_time(self, gain_index: int, speed_index: int) -> None:
        ret = self.lib.SetAdaptiveIntegrationTime(gain_index, speed_index)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_GAIN, _Error.PARAM_ERR_INT_TIME))

    def _set_averaging_number_of_scan(self, n_scans: int) -> None:
        ret = self.lib.SetAveragingNumberOfScan(n_scans)
        # this function is not in the SDK manual
        # so not sure what error codes it can return
        self._check(ret, ())

    def _set_dark_current_params(self, mode: int, wavelength: float) -> None:
        ret = self.lib.SetDarkCurrentParams(mode, wavelength)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_DC_MODE, _Error.PARAM_ERR_DC_WAVE))

    def _set_gain(self, scan_mode: int, gain_index: int) -> None:
        ret = self.lib.SetGain(scan_mode, gain_index)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_GAIN, _Error.PARAM_ERR_SCAN_MODE))

    def _set_integration_time(self, scan_mode: int, scan_speed: int) -> None:
        ret = self.lib.SetIntegrationTime(scan_mode, scan_speed)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_SCAN_MODE, _Error.PARAM_ERR_INT_TIME))

    def _set_pmt_flux_overload_voltage(self, voltage: float) -> None:
        ret = self.lib.SetPMTFluxOverloadVoltage(voltage)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_OVERLOAD))

    def _set_pmt_high_voltage(self, voltage: float) -> None:
        ret = self.lib.SetPMTHiVoltage(voltage)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_OVERLOAD))

    # def _set_pmt_settling_time(self, time: int) -> None:
    #     """Set the settling time of the photomultiplier tube.
    #
    #     Not in the SDK manual.
    #
    #     Args:
    #         time: Settling Time in seconds.
    #     """
    #     ret = self.lib.SetPmtSettlingTime(time)  # noqa: ERA001
    #     self._check(ret, ())  # noqa: ERA001

    def _set_reference_white_point(self, white: int, x: float, y: float) -> None:
        ret = self.lib.SetReferenceWhitePoint(white, x, y)
        self._check(ret, ())

    def _set_scan_range(self, start: float, end: float, increment_index: int) -> None:
        ret = self.lib.SetScanRange(start, end, increment_index)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.PARAM_ERR_WAVE_RANGE, _Error.PARAM_ERR_WAVE_INC))

    def _set_settling_time(self, time: float) -> None:
        ret = self.lib.SetSettlingTime(time)
        self._check(ret, (_Error.SYSTEM_BUSY,))

    def _set_tab_delimited_mode(self, enable: bool) -> None:  # noqa: FBT001
        self.lib.SetTabDelimitedMode(enable)

    def _set_user_defined_integration_time(self, time: float) -> None:
        ret = self.lib.SetUserDefinedIntegrationTime(time)
        self._check(ret, (_Error.PARAM_ERR_INT_TIME,))

    def _stop_measurement(self) -> None:
        ret = self.lib.StopMeasurement()
        self._check(ret, ())

    def _take_point_to_point_calibration(self, meas_type: int) -> None:
        ret = self.lib.TakePointToPointCalibration(meas_type)
        self._check(
            ret,
            (
                _Error.SYSTEM_BUSY,
                _Error.SYSTEM_NOT_CONNECTED,
                _Error.SCAN_PARAMS_NOT_SENT,
                _Error.SCAN_CANCELLED,
                _Error.SCAN_FLUX_OVERLOAD,
                _Error.PARAM_ERR_MEAS_TYPE,
            ),
        )

    def _take_point_to_point_measurement(self, meas_type: int) -> None:
        ret = self.lib.TakePointToPointMeasurement(meas_type)
        self._check(
            ret,
            (
                _Error.SYSTEM_BUSY,
                _Error.SYSTEM_NOT_CONNECTED,
                _Error.SCAN_PARAMS_NOT_SENT,
                _Error.SCAN_CANCELLED,
                _Error.SCAN_FLUX_OVERLOAD,
                _Error.PARAM_ERR_MEAS_TYPE,
            ),
        )

    def _take_quick_scan_calibration(self, meas_type: int) -> None:
        ret = self.lib.TakeQuickScanCalibration(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.SCAN_PARAMS_NOT_SENT))

    def _take_quick_scan_measurement(self, meas_type: int) -> None:
        ret = self.lib.TakeQuickScanMeasurement(meas_type)
        self._check(ret, (_Error.SYSTEM_BUSY, _Error.SYSTEM_NOT_CONNECTED, _Error.SCAN_PARAMS_NOT_SENT))

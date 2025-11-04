"""Communicate with an OL 756 spectroradiometer from [Optronic Laboratories](https://optroniclabs.com/)."""

from __future__ import annotations

import contextlib
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from msl.loadlib import Client64, ConnectionTimeoutError, Server32Error

from msl.equipment.interfaces import MSLConnectionError
from msl.equipment.schema import Interface
from msl.equipment.utils import logger

if TYPE_CHECKING:
    from typing import Any, Callable, Literal

    from numpy.typing import NDArray

    from msl.equipment._types import PathLike
    from msl.equipment.schema import Equipment


class OL756(Interface, manufacturer=r"Optronic", model=r"(OL)?\s*756", flags=re.IGNORECASE):
    """Communicate with an OL 756 spectroradiometer from [Optronic Laboratories](https://optroniclabs.com/)."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with an OL 756 spectroradiometer from Optronic Laboratories.

        This class can be used with either a 32- or 64-bit Python interpreter
        to call the 32-bit functions in the `OL756SDKActiveXCtrl` library.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following
        _properties_ for an OL 756 spectroradiometer.

        Attributes: Connection Properties:
            mode (int): Connection mode (`0`: RS-232, `1`: USB). _Default: `1` (USB)_
            com_port (int): The COM port number (RS-232 mode only). _Default: `1`_
        """
        self._client: Client64 | None = None
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101

        try:
            self._client = Client64(
                Path(__file__).parent / "ol756ocx_32.py",
                prog_id=equipment.connection.address[5:],
                mode=equipment.connection.properties.get("mode", 1),
                com_port=equipment.connection.properties.get("com_port", 1),
            )
        except ConnectionTimeoutError as e:
            msg = f"Cannot initialize the OL756 SDK.\n{e.reason}"
            raise MSLConnectionError(self, msg) from None

        self._request32: Callable[..., Any] = self._client.request32

        if self._request32("mode") == -1:
            self.disconnect()
            msg = "Cannot connect to the OL756 spectroradiometer. Is it turned on and connected to the computer?"
            raise MSLConnectionError(self, msg) from None

    def _send(self, attr: str, *args: Any) -> Any:  # noqa: ANN401
        """Send a request to the OCX library."""
        try:
            logger.debug("OL756.%s%s", attr, args)
            return self._request32(f"_{attr}", *args)
        except Server32Error as e:
            raise MSLConnectionError(self, e.traceback) from None

    def accumulate_signals(self, meas_type: Literal[0, 1, 2, 3, 4, 5]) -> None:
        """Function needs to be called after a measurement was performed.

        This essentially accumulates the data together until the user is
        ready to average out the data. This function is used in combination with
        [reset_averaging][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.reset_averaging]
        and [do_averaging][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.do_averaging].

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance
                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

        """
        self._send("accumulate_signals", meas_type)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the OL756 spectroradiometer."""
        if self._client is None:
            return

        with contextlib.suppress(Server32Error):
            self._send("connect_to_ol756", -1)

        try:
            stdout, stderr = self._client.shutdown_server32()
        except Server32Error:
            pass
        else:
            stdout.close()
            stderr.close()

        self._client = None
        super().disconnect()

    def do_averaging(self, meas_type: Literal[0, 1, 2, 3, 4, 5], n_scans: int) -> None:
        """Function divides the accumulated signal by the number of scans performed.

        It then sets the array containing the data with the averaged data. This function is used in combination with
        [reset_averaging][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.reset_averaging]
        and [accumulate_signals][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.accumulate_signals].

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance
                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

            n_scans: The number of scans to average.
        """
        self._send("do_averaging", meas_type, n_scans)

    def do_calculations(self, meas_type: Literal[0, 1, 2, 3, 4, 5]) -> None:
        """Function needs to be called after each measurement to update the calculations.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance
                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

        """
        self._send("do_calculations", meas_type)

    def enable_calibration_file(self, meas_type: Literal[3, 4, 5], *, enable: bool) -> None:
        """Enables or disables the use of a calibration file.

        Use this option to generate calibrated results. To open a standard file
        used to create a calibration, use
        [enable_standard_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.enable_standard_file]
        instead.

        The user should call
        [load_calibration_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.load_calibration_file]
        first to load the calibration file before enabling it.

        Args:
            meas_type: The measurement type.

                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

            enable: Whether to enable or disable the use of a calibration file.
        """
        self._send("enable_calibration_file", meas_type, enable)

    # def enable_dark_compensation(self):
    #     # EnableDarkCompensation -- not in SDK manual
    #     raise NotImplementedError

    def enable_dark_current(self, *, enable: bool = True) -> None:
        """Turn the dark current on or off.

        Enable this feature if you want the dark current automatically
        acquired and subtracted before each measurement. If you wish to
        take a dark current manually, see the
        [get_dark_current][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.get_dark_current]
        function.

        The parameters for the dark current will need to be set using
        [set_dark_current_params][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_dark_current_params].

        Args:
            enable: Whether to turn the dark current on or off.
        """
        self._send("enable_dark_current", enable)

    def enable_pmt_protection_mode(self, *, enable: bool) -> None:
        """Turn the PMT protection routines on or off.

        Enable this feature if you want the PMT to be shielded while travelling
        through high intensity spikes. This feature will make the scan slower
        since the wavelength and filter drive will move asynchronously.

        The PMT is still protected by the hardware. This function prevents
        exposure of the PMT while travelling.

        Args:
            enable: Whether to turn the PMT protection routines on or off.
        """
        self._send("enable_pmt_protection_mode", enable)

    def enable_standard_file(self, meas_type: Literal[0, 1, 2], *, enable: bool) -> None:
        """Function enables standard files to be used.

        To open a calibration file used to create a measurement, use
        [enable_calibration_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.enable_calibration_file]
        instead.

        The user should call
        [load_standard_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.load_standard_file]
        first to load the standard file before enabling it.

        Args:
            meas_type: The calibration measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance

            enable: Whether to turn the application of the standard file on or off.
        """
        self._send("enable_standard_file", meas_type, enable)

    def export_config_file(self, file_path: PathLike) -> None:
        """Exports the config file into a OL756 compatible configuration file.

        Not all settings used will be applicable.

        Args:
            file_path: A valid path to save the file at.
        """
        self._send("export_config_file", os.fsdecode(file_path))

    def export_registry(self) -> None:
        """Save data out to the Windows registry.

        Make sure that a read was done at some point using
        [import_registry][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.import_registry].
        Does not create a configuration file that can be loaded into another computer. For that particular function,
        call [export_config_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.export_config_file].
        """
        self._send("export_registry")

    def get_adaptive_int_time_index(self, gain_index: int) -> int:
        """Get the adaptive integration time index.

        Args:
            gain_index: The index of the gain to use to get the integration time.

                * `0` &mdash; 1.0E-5
                * `1` &mdash; 1.0E-6
                * `2` &mdash; 1.0E-7
                * `3` &mdash; 1.0E-8
                * `4` &mdash; 1.0E-9
                * `5` &mdash; 1.0E-10
                * `6` &mdash; 1.0E-11

        Returns:
            The adaptive integration time index.
        """
        index = int(self._send("get_adaptive_int_time_index", gain_index))
        if index == -1:
            msg = f"Invalid gain index, {gain_index}"
            raise MSLConnectionError(self, msg)
        return index

    def get_cri(self, meas_type: Literal[0, 1, 2, 3, 4, 5], index: int) -> float:
        """Get the color-rendering information.

        The user should call
        [do_calculations][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.do_calculations]
        at least once before calling this function.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance
                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

            index: The color-rendering index.

                * `0` &mdash; General CRI
                * `1` &mdash; Light Greyish Red (CRI#1)
                * `2` &mdash; Dark Greyish Yellow (CRI#2)
                * `3` &mdash; Strong Yellow Green (CRI#3)
                * `4` &mdash; Moderate Yellowish Green (CRI#4)
                * `5` &mdash; Light Bluish Green (CRI#5)
                * `6` &mdash; Light Blue (CRI#6)
                * `7` &mdash; Light Violet (CRI#7)
                * `8` &mdash; Light Reddish Purple (CRI#8)
                * `9` &mdash; Strong Red (CRI#9)
                * `10` &mdash; Strong Yellow (CRI#10)
                * `11` &mdash; Strong Green (CRI#11)
                * `12` &mdash; Strong Blue (CRI#12)
                * `13` &mdash; Light Yellowish Pink (CRI#13)
                * `14` &mdash; Moderate Olive Green (CRI#14)

        Returns:
            The color-rendering information.
        """
        return float(self._send("get_cri", meas_type, index))

    def get_cal_array(self) -> NDArray[np.int32]:
        """This method allows user to get the spectral data of a calibration after it is made.

        Returns:
            The calibrated spectral data.
        """
        return np.array(self._send("get_cal_array"))

    def get_cal_file_enabled(self, meas_type: Literal[3, 4, 5]) -> bool:
        """Checks to see if the calibration file is enabled.

        The user should call
        [load_calibration_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.load_calibration_file]
        first to load the calibration file before enabling it.

        Args:
            meas_type: The measurement type.

                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

        Returns:
            Whether the calibration file is enabled.
        """
        return bool(self._send("get_cal_file_enabled", meas_type))

    def get_calculated_data(self, meas_type: Literal[0, 1, 2, 3, 4, 5], index: int) -> float:
        """Get data calculated from the intensities.

        The user should call
        [do_calculations][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.do_calculations]
        at least once before calling this function.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance
                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

            index: The index to retrieve data of.

                * `0` &mdash; Color Temperature
                * `1` &mdash; Dominant Wavelength
                * `2` &mdash; LED Half Bandwidth
                * `3` &mdash; Left Half Bandwidth
                * `4` &mdash; Right Half Bandwidth
                * `5` &mdash; Peak Spectral Value
                * `6` &mdash; LEDPeakWavelength
                * `7` &mdash; Radiometric Value
                * `8` &mdash; Purity
                * `9` &mdash; Center Wavelength
                * `10` &mdash; Photometric Value

        Returns:
            The calculated data.
        """
        return float(self._send("get_calculated_data", meas_type, index))

    def get_calibration_file(self, meas_type: Literal[0, 1, 2]) -> str:
        """Get a calibration file that is loaded.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance

        Returns:
            String containing the name and path of the calibration file
                that is loaded for a particular measurement type.
        """
        return str(self._send("get_calibration_file", meas_type))

    def get_chromaticity_data(self, meas_type: Literal[0, 1, 2, 3, 4, 5], index: int) -> float:
        """Get the calculated chromaticity values requested.

        Must have called [do_calculations][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.do_calculations]
        at least once.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance
                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

            index: The chromaticity index value [0..70]. See the SDK manual for more details.

        Returns:
            The chromaticity data.
        """
        return float(self._send("get_chromaticity_data", meas_type, index))

    # def get_dc_adj_raw_sig_variant_array(self):
    #     # GetDCAdjRawSigVariantArray -- not in SDK manual
    #     raise NotImplementedError

    # def get_dc_adjusted_raw_signal_array(self):
    #     # GetDCAdjustedRawSignalArray -- not in SDK manual
    #     raise NotImplementedError

    # def get_dark_compensation_enable(self):
    #     # GetDarkCompensationEnable -- not in SDK manual
    #     raise NotImplementedError

    def get_dark_current(self, use_compensation: int) -> float:
        """Takes a manual dark current.

        User will have to subtract from data array by retrieving this array via
        a [get_cal_array][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.get_cal_array] or
        [get_signal_array][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.get_signal_array].
        This is a special function and most users will want to use
        [enable_dark_current][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.enable_dark_current]
        instead because it automatically does the subtraction.

        Function if called externally by user program will not have result
        saved out to data file. If the
        [enable_dark_current][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.enable_dark_current]
        was enabled, then this function need should not be called.

        Args:
            use_compensation: Adjusts dark current for more dynamic ranging using reverse current.

        Returns:
            The dark current.
        """
        return float(self._send("get_dark_current", use_compensation))

    def get_dark_current_enable(self) -> bool:
        """Returns whether the dark-current mode is enabled.

        Returns:
            Whether the dark-current mode is enabled or disabled.
        """
        return bool(self._send("get_dark_current_enable"))

    def get_dark_current_mode(self) -> int:
        """Returns whether the dark current is taken at a wavelength or in shutter mode.

        Returns:
            The dark-current mode.

                * `0` &mdash; Dark current in wavelength mode (taken at a particular wavelength designated by the user).
                * `1` &mdash; Dark current in shutter mode

        """
        return int(self._send("get_dark_current_mode"))

    def get_dark_current_wavelength(self) -> float:
        """Get the dark current wavelength.

        Returns:
            Wavelength that the dark current will be taken at.
        """
        return float(self._send("get_dark_current_wavelength"))

    def get_ending_wavelength(self) -> float:
        """Get the ending wavelength of the scan range.

        Returns:
            The ending wavelength, in nm, of the scan range.
        """
        return float(self._send("get_ending_wavelength"))

    def get_gain_index(self) -> int:
        """Get the index of the gain that will be applied when the parameters are to be sent down.

        Applies to both quick scan and point to point scans.

        Returns:
            The gain index.

                * `0` &mdash; 1.0E-5
                * `1` &mdash; 1.0E-6
                * `2` &mdash; 1.0E-7
                * `3` &mdash; 1.0E-8
                * `4` &mdash; 1.0E-9
                * `5` &mdash; 1.0E-10 (Point to Point mode only)
                * `6` &mdash; 1.0E-11 (Point to Point mode only)
                * `7` &mdash; Auto Gain Ranging (Point to Point mode only)

        """
        return int(self._send("get_gain_index"))

    def get_increment(self) -> float:
        """Get the wavelength increment that is used for a scan.

        Returns:
            The wavelength increment, in nm.
        """
        return float(self._send("get_increment"))

    def get_increment_index(self) -> int:
        """Get the index of the wavelength increment that is used for a scan.

        Applies to both quick scan and point to point scans.

        Returns:
            Index of the wavelength increment of a scan.

                * `0` &mdash; 0.025 nm
                * `1` &mdash; 0.05 nm
                * `2` &mdash; 0.1 nm
                * `3` &mdash; 0.2 nm
                * `4` &mdash; 0.5 nm
                * `5` &mdash; 1.0 nm
                * `6` &mdash; 2.0 nm
                * `7` &mdash; 5.0 nm
                * `8` &mdash; 10.0 nm

        """
        return int(self._send("get_increment_index"))

    def get_integration_time_index(self, scan_mode: Literal[0, 1]) -> int:
        """Get the index into the integration time array.

        Applies to both quick scan and point to point scans. In quick scan,
        the speed will vary based on the scan range and increments.

        Args:
            scan_mode: The scan mode to use to get the index of.
                Point to Point mode (0) or Quick Scan mode (1).

        Returns:
            Point to Point mode

                * `0` &mdash; 1.000 sec
                * `1` &mdash; 0.500 sec
                * `2` &mdash; 0.200 sec
                * `3` &mdash; 0.100 sec
                * `4` &mdash; 0.050 sec
                * `5` &mdash; 0.020 sec
                * `6` &mdash; 0.010 sec
                * `7` &mdash; 0.005 sec
                * `8` &mdash; 0.002 sec
                * `9` &mdash; 0.001 sec
                * `10` &mdash; Adaptive	(Point To Point mode only)

                Quick Scan mode

                    * `0` &mdash; slowest
                    * `10` &mdash; fastest

        """
        return int(self._send("get_integration_time_index", scan_mode))

    def get_ocx_version(self) -> str:
        """Get the version of the OL756 SDK ActiveX control.

        Returns:
            The software version.
        """
        return str(self._send("get_ocx_version"))

    def get_pmt_flux_overload(self) -> float:
        """Get the voltage of the photomultiplier tube flux overload.

        Returns:
            Voltage that the PMT will determine to be at the overload point.
        """
        return float(self._send("get_pmt_flux_overload"))

    # def get_pmt_protection_mode(self):
    #     # GetPMTProtectionMode -- not in SDK manual
    #     raise NotImplementedError

    # def get_pmt_settling_time(self):
    #     # GetPmtSettlingTime -- not in SDK manual
    #     raise NotImplementedError

    def get_pmt_voltage(self) -> float:
        """Returns the voltage that will sent or has been sent down to the PMT.

        Returns:
            Voltage value, in volts, of the photomultiplier tube.
        """
        return float(self._send("get_pmt_voltage"))

    def get_quick_scan_rate(self) -> float:
        """Returns the rate at the quick scan index.

        Returns:
            Rate of the quick scan at the current index in nm/s.
        """
        return float(self._send("get_quick_scan_rate"))

    def get_quick_scan_rate_index(self) -> int:
        """Returns the index of the quick scan rate.

        Returns:
            Index of the quick scan rate.
        """
        return int(self._send("get_quick_scan_rate_index"))

    # def get_raw_signal_array(self):
    #     # GetRawSignalArray -- not in SDK manual
    #     raise NotImplementedError

    # def get_raw_signal_variant_array(self):
    #     # GetRawSignalVariantArray -- not in SDK manual
    #     raise NotImplementedError

    def get_scan_mode(self) -> int:
        """Get the mode the scan will be done in.

        Returns:
            The scan mode.

                * `0` &mdash; Point to Point mode
                * `1` &mdash; Quick Scan mode

        """
        return int(self._send("get_scan_mode"))

    def get_settling_time(self) -> float:
        """Get the settling time.

        Settling time is time where the wavelength drive pauses once it reaches its target wavelength.

        Returns:
            Settling time, in seconds, to be sent down or has already been sent to the system.
        """
        return float(self._send("get_settling_time"))

    def get_signal_array(self) -> NDArray[np.int32]:
        """Get the spectral data of a measurement after it is made.

        Returns:
            The spectral data.
        """
        return np.array(self._send("get_signal_array"))

    def get_standard_file(self, meas_type: Literal[3, 4, 5]) -> str:
        """Retrieves the name of standard file.

        Args:
            meas_type: The calibration measurement type.

                * `3` &mdash; Irradiance calibration
                * `4` &mdash; Radiance calibration
                * `5` &mdash; Transmittance calibration

        Returns:
            String containing the name and path of the standard file that is
                loaded for a particular calibration type.
        """
        return str(self._send("get_standard_file", meas_type))

    def get_start_wavelength(self) -> float:
        """Get the starting wavelength of a scan.

        Applies to both quick scan and point to point scans.

        Returns:
            The wavelength, in nm, that the scan will start from.
        """
        return float(self._send("get_start_wavelength"))

    def get_std_file_enabled(self, meas_type: Literal[0, 1, 2]) -> bool:
        """Checks to see if the standard file is enabled.

        The user should call
        [load_standard_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.load_standard_file]
        first to load the standard file before enabling it.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance

        Returns:
            Whether a standard file is enabled.
        """
        return bool(self._send("get_std_file_enabled", meas_type))

    def import_config_file(self, path: PathLike) -> None:
        """The file is a standard OL756 configuration file.

        Not all settings used will be applicable. Measurement type is not used
        because in the SDK, the
        [take_point_to_point_measurement][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.take_point_to_point_measurement]
        function has as an input the measurement type. The user should select
        the type and not have it based on the configuration file.

        Args:
            path: A valid path to load the file at.
        """
        self._send("import_config_file", os.fsdecode(path))

    def import_registry(self) -> None:
        """Loads data from the registry.

        Loads default if no registry exists. To import the configuration
        from another computer, use
        [import_config_file][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.import_config_file]
        instead.

        Not all settings used will be applicable. Measurement type is not
        used because in the SDK, the
        [take_point_to_point_measurement][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.take_point_to_point_measurement]
        function has as an input the measurement type. The user should
        select the type and not have it based on the configuration file.
        """
        self._send("import_registry")

    # def init_sdk(self):
    #     # InitSDK -- not in the SDK manual
    #     raise NotImplementedError

    def load_calibration_file(self, path: PathLike, meas_type: Literal[3, 4, 5]) -> None:
        """Load a calibration file.

        Args:
            path: The path of a calibration file.
            meas_type: The calibration measurement type.

                * `3` &mdash; Irradiance calibration
                * `4` &mdash; Radiance calibration
                * `5` &mdash; Transmittance calibration

        """
        self._send("load_calibration_file", os.fsdecode(path), meas_type)

    def load_standard_file(self, path: PathLike, meas_type: Literal[0, 1, 2]) -> None:
        """Load a standard file.

        Args:
            path: The path of a standard file.
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance

        """
        self._send("load_standard_file", os.fsdecode(path), meas_type)

    def manual_filter_drive_connect(self, *, connect: bool) -> None:
        """Used to connect or disconnect the filter drive.

        Disconnecting essentially acquires scans without the filter.

        Args:
            connect: Connect or disconnect the filter drive. Reconnecting will
                home the wavelength and filter drive.
        """
        self._send("manual_filter_drive_connect", connect)

    def manual_get_gain(self) -> int:
        """The index of the gain that will be applied when the parameters are to be sent down.

        Returns:
            The gain index.

                * `0` &mdash; 1.0E-5
                * `1` &mdash; 1.0E-6
                * `2` &mdash; 1.0E-7
                * `3` &mdash; 1.0E-8
                * `4` &mdash; 1.0E-9
                * `5` &mdash; 1.0E-10 (Point to Point mode only)
                * `6` &mdash; 1.0E-11 (Point to Point mode only)
                * `7` &mdash; Auto Gain Ranging (Point to Point mode only)

        """
        return int(self._send("manual_get_gain"))

    def manual_get_integration_time(self) -> float:
        """Returns the integration time set in the system.

        Only applies to the integration time used for Point to Point scans.

        Returns:
            The integration time in seconds.
        """
        return float(self._send("manual_get_integration_time"))

    def manual_get_pmt_overload(self) -> float:
        """Returns the PMT overload voltage set in the system.

        Returns:
            Overload voltage, in volts, of the photomultiplier tube.
        """
        return float(self._send("manual_get_pmt_overload"))

    def manual_get_pmt_voltage(self) -> float:
        """Returns the PMT high voltage set in the system.

        Returns:
            Voltage, in volts, of the photomultiplier tube.
        """
        return float(self._send("manual_get_pmt_voltage"))

    def manual_get_settling_time(self) -> float:
        """Returns the settling time of the instrument.

        Returns:
            Settling time of the system in seconds.
        """
        return float(self._send("manual_get_settling_time"))

    def manual_get_signal(self) -> float:
        """Returns the signal at the current position of the wavelength drive.

        Returns:
            The signal, in amperes.
        """
        return float(self._send("manual_get_signal"))

    def manual_home_ol756(self) -> None:
        """Homes the wavelength and filter drive.

        Will reconnect the filter drive if it was disconnected
        """
        self._send("manual_home_ol756")

    def manual_move_to_wavelength(self, wavelength: float) -> None:
        """Moves the wavelength drive to a particular location.

        Args:
            wavelength: The wavelength to move the wavelength drive to.
        """
        self._send("manual_move_to_wavelength", wavelength)

    def manual_set_gain(self, gain_index: int, mode: int) -> None:
        """Set the gain.

        Args:
            gain_index: The gain index.

                * `0` &mdash; 1.0E-5
                * `1` &mdash; 1.0E-6
                * `2` &mdash; 1.0E-7
                * `3` &mdash; 1.0E-8
                * `4` &mdash; 1.0E-9
                * `5` &mdash; 1.0E-10 (Point to Point mode only)
                * `6` &mdash; 1.0E-11 (Point to Point mode only)
                * `7` &mdash; Auto Gain Ranging (Point to Point mode only)

            mode: The scan mode.

                * `0` &mdash; Point to point
                * `1` &mdash; Quick scan
        """
        self._send("manual_set_gain", gain_index, mode)

    def manual_set_integration_time(self, time: float) -> None:
        """Sets the integration time set in the system.

        Only applies to the integration time used for Point to Point scans.

        Args:
            time: The integration time in seconds.
        """
        self._send("manual_set_integration_time", time)

    def manual_set_pmt_overload(self, overload: float) -> None:
        """Sets the PMT overload voltage set in the system.

        Args:
            overload: Overload voltage, in volts, of the photomultiplier tube in Volts.
        """
        self._send("manual_set_pmt_overload", overload)

    def manual_set_pmt_voltage(self, voltage: float) -> None:
        """Sets the PMT high voltage set in the system.

        Args:
            voltage: Voltage, in volts, of the photomultiplier tube.
        """
        self._send("manual_set_pmt_voltage", voltage)

    def manual_set_settling_time(self, time: float) -> None:
        """Sets the settling time of the instrument.

        Args:
            time: Settling time of the system.
        """
        self._send("manual_set_settling_time", time)

    def move_to_wavelength(self, wavelength: float) -> None:
        """Moves the wavelength drive to a particular location.

        Args:
            wavelength: The wavelength, in nm, to move the wavelength drive to.
        """
        self._send("move_to_wavelength", wavelength)

    def read_ol756_flash_settings(self) -> None:
        """Reads the saved settings from the flash memory.

        Reads the settings such as the grating alignment factor, filter skew
        and wavelength skew. Loads these values into the ActiveX control memory.
        """
        self._send("read_ol756_flash_settings")

    def reset_averaging(self, meas_type: Literal[0, 1, 2, 3, 4, 5]) -> None:
        """Resets the accumulated signal array for the specified measurement type.

        This function is used in combination with
        [do_averaging][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.do_averaging]
        and [accumulate_signals][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.accumulate_signals].

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance
                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

        """
        self._send("reset_averaging", meas_type)

    def save_calibration_file(self, meas_type: Literal[3, 4, 5], path: PathLike) -> None:
        """Create a OL756-compatible calibration file.

        Args:
            meas_type: The calibration measurement type.

                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

            path: The path to save the calibration file to.
        """
        self._send("save_calibration_file", meas_type, os.fsdecode(path))

    def save_measurement_data(self, meas_type: Literal[0, 1, 2], path: PathLike) -> None:
        """Save the measurement data to a OL756-compatible data file.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance

            path: The path to save the data to.
        """
        self._send("save_measurement_data", meas_type, os.fsdecode(path))

    def send_down_parameters(self, scan_mode: Literal[0, 1]) -> None:
        """Sends down the parameters to the system.

        This needs to be called whenever parameters dealing with the PMT or
        integration time and gain has changed. Needs to be called once before
        doing any measurements or other signal acquisition including dark
        current.

        The following methods affect the parameters

        * [set_pmt_flux_overload_voltage][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_pmt_flux_overload_voltage]
        * [set_gain][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_gain]
        * [set_integration_time][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_integration_time]
        * [set_pmt_high_voltage][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_pmt_high_voltage]
        * [set_settling_time][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_settling_time]
        * [set_scan_range][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_scan_range]
        * [set_adaptive_integration_time][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.set_adaptive_integration_time]

        Args:
            scan_mode: The scan mode.

                * `0` &mdash; Point to point
                * `1` &mdash; Quick scan

        """  # noqa: E501
        self._send("send_down_parameters", scan_mode)

    def set_adaptive_integration_time(self, gain_index: int, speed_index: int) -> None:
        """Sets the scan speed of the scan at a particular gain range.

        Adaptive integration time is used solely for point to point
        scans in auto-gain ranging.

        Args:
            gain_index: The index of the gain to use to set the integration time.

                * `0` &mdash; 1.0E-5
                * `1` &mdash; 1.0E-6
                * `2` &mdash; 1.0E-7
                * `3` &mdash; 1.0E-8
                * `4` &mdash; 1.0E-9
                * `5` &mdash; 1.0E-10
                * `6` &mdash; 1.0E-11

            speed_index: The scan speed index [0..12] &mdash; `0` (Slowest), `12` (Fastest).
        """
        self._send("set_adaptive_integration_time", gain_index, speed_index)

    def set_averaging_number_of_scan(self, n_scans: int) -> None:
        """Set the number of scans to average.

        Args:
            n_scans: The number of scans to average.
        """
        self._send("set_averaging_number_of_scan", n_scans)

    def set_dark_current_params(self, mode: Literal[0, 1], wavelength: float) -> None:
        """Sets the mode and the wavelength to use for a dark-current measurement.

        Args:
            mode: The mode to use to acquire a dark-current measurement.

                * `0` &mdash; wavelength
                * `1` &mdash; shutter

            wavelength: The wavelength, in nm, to use for a dark-current measurement.
        """
        self._send("set_dark_current_params", mode, wavelength)

    def set_gain(self, scan_mode: Literal[0, 1], gain_index: int) -> None:
        """Sets the index of the gain that will be applied when the parameters are to be sent down.

        Applies to both quick scan and point to point scans.

        Args:
            scan_mode: The scan mode.

                * `0` &mdash; Point to Point
                * `1` &mdash; Quick Scan

            gain_index: The gain index.

                * `0` &mdash; 1.0E-5
                * `1` &mdash; 1.0E-6
                * `2` &mdash; 1.0E-7
                * `3` &mdash; 1.0E-8
                * `4` &mdash; 1.0E-9
                * `5` &mdash; 1.0E-10 (available only in Point to Point mode)
                * `6` &mdash; 1.0E-11 (available only in Point to Point mode)
                * `7` &mdash; Auto Gain Ranging (available only in Point to Point mode)

        """
        self._send("set_gain", scan_mode, gain_index)

    def set_integration_time(self, scan_mode: Literal[0, 1], scan_speed: int) -> None:
        """Sets the index of the scan speed used.

        Applies to both quick scan and point to point scans.
        In quick scan, the speed will vary based on the scan range and increments.

        Args:
            scan_mode: The scan mode.

                * `0` &mdash; Point to Point
                * `1` &mdash; Quick Scan

            scan_speed: Index to the integration time array.

                Point to Point mode.

                * `0` &mdash; 1.000 sec
                * `1` &mdash; 0.500 sec
                * `2` &mdash; 0.200 sec
                * `3` &mdash; 0.100 sec
                * `4` &mdash; 0.050 sec
                * `5` &mdash; 0.020 sec
                * `6` &mdash; 0.010 sec
                * `7` &mdash; 0.005 sec
                * `8` &mdash; 0.002 sec
                * `9` &mdash; 0.001 sec
                * `10` &mdash; Adaptive	(Point To Point mode only)
                * `11` &mdash; User defined (Point To Point mode only)

                Quick Scan mode.

                * `0` &mdash; slowest
                * `10` &mdash; fastest

        """
        self._send("set_integration_time", scan_mode, scan_speed)

    def set_pmt_flux_overload_voltage(self, voltage: float) -> None:
        """Sets the value to use for the photomultiplier tube flux overload.

        Args:
            voltage: Voltage that the PMT will determine to be at the overload point.
                Software only, because PMT has built-in protection also.
        """
        self._send("set_pmt_flux_overload_voltage", voltage)

    def set_pmt_high_voltage(self, voltage: float) -> None:
        """Sets the value to be determined to be a flux overload by the software.

        Args:
            voltage: Voltage, in volts, that the PMT will determine to be overload point.
        """
        self._send("set_pmt_high_voltage", voltage)

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
    #     ret = self.lib.SetPmtSettlingTime(time)  # noqa: ERA001
    #     self._check(ret, ())  # noqa: ERA001

    def set_reference_white_point(self, white: Literal[0, 1, 2, 3, 4, 5], x: float, y: float) -> None:
        """Sets the value of the reference illuminant.

        Args:
            white: The reference white point.

                * `0` &mdash; Incandescent (A)
                * `1` &mdash; Direct Sunlight (B)
                * `2` &mdash; Indirect Sunlight (C)
                * `3` &mdash; Natural Daylight (D65)
                * `4` &mdash; Normalized Reference (E)
                * `5` &mdash; User Defined

            x: User defined x value on CIE chart.
            y: User defined y value on CIE chart.
        """
        self._send("set_reference_white_point", white, x, y)

    def set_scan_range(self, start: float, end: float, increment_index: int) -> None:
        """Sets the wavelength scan range.

        Args:
            start: Starting wavelength, in nm.
            end: Ending wavelength, in nm.
            increment_index: Increment index, see
                [get_increment_index][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.get_increment_index].
        """
        self._send("set_scan_range", start, end, increment_index)

    def set_settling_time(self, time: float) -> None:
        """Set the settling time.

        Settling time is the time that the wavelength drive pauses once
        it reaches its target wavelength.

        Args:
            time: Settling Time in seconds to be sent down or has already been sent to the system.
        """
        self._send("set_settling_time", time)

    def set_tab_delimited_mode(self, *, enable: bool) -> None:
        """Purpose of function is to set what mode to write the data files as.

        Setting the tab delimited to true will write the data in a tab
        delimited format, else a false will write in a comma delimited format.
        Tab delimited files will not be compatible with some versions of the
        software. If you want data files to be compatible with v1.32 software
        and below, leave the mode to `False`.

        Args:
            enable: Whether to use the new file format using TABs as a delimited or
                the old file format compatible with v1.32 and below.
        """
        self._send("set_tab_delimited_mode", enable)

    def set_user_defined_integration_time(self, time: float) -> None:
        """Sets the user defined integration time.

        Used only in point to point scans and only if the user sets the integration time mode.

        Args:
            time: Integration time in seconds.
        """
        self._send("set_user_defined_integration_time", time)

    def stop_measurement(self) -> None:
        """Stops a measurement.

        Applies only to Point to Point measurements. Quick scans are done
        so quickly that there is no need to stop a measurement once it starts.
        """
        self._send("stop_measurement")

    def take_point_to_point_calibration(self, meas_type: Literal[3, 4, 5]) -> None:
        """Takes a calibration in point to point mode.

        Need to have called
        [send_down_parameters][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.send_down_parameters]
        at least once before calling any of the measurement functions or data acquisition functions.

        Args:
            meas_type: The calibration measurement type.

                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

        """
        self._send("take_point_to_point_calibration", meas_type)

    def take_point_to_point_measurement(self, meas_type: Literal[0, 1, 2]) -> None:
        """Takes a measurement in point to point mode.

        Need to have called
        [send_down_parameters][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.send_down_parameters]
        at least once before calling any of the measurement functions or data acquisition functions.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance

        """
        self._send("take_point_to_point_measurement", meas_type)

    def take_quick_scan_calibration(self, meas_type: Literal[3, 4, 5]) -> None:
        """Takes a calibration in quick scan mode.

        Need to have called
        [send_down_parameters][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.send_down_parameters]
        at least once before calling any of the measurement functions or data acquisition functions.

        Args:
            meas_type: The calibration measurement type.

                * `3` &mdash; Irradiance Calibration
                * `4` &mdash; Radiance Calibration
                * `5` &mdash; Transmittance Calibration

        """
        self._send("take_quick_scan_calibration", meas_type)

    def take_quick_scan_measurement(self, meas_type: Literal[0, 1, 2]) -> None:
        """Takes a measurement in quick scan mode.

        Need to have called
        [send_down_parameters][msl.equipment_resources.optronic_labs.ol756ocx_64.OL756.send_down_parameters]
        at least once before calling any of the measurement functions or data acquisition functions.

        Args:
            meas_type: The measurement type.

                * `0` &mdash; Irradiance
                * `1` &mdash; Radiance
                * `2` &mdash; Transmittance

        """
        self._send("take_quick_scan_measurement", meas_type)

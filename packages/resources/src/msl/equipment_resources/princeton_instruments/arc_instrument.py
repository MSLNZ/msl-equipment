"""Wrapper around the `ARC_Instrument.dll` SDK from [Princeton Instruments]{:target="_blank"}.

The wrapper was written using v2.0.3 of the SDK.

Applicable for monochromator/spectrographs, filter wheels and readout systems (NCL/NCL-Lite)
from [Princeton Instruments]{:target="_blank"}.

[Princeton Instruments]: https://www.princetoninstruments.com/
"""

# cSpell: ignore readall nonblock gadjust Grat Focallength eeoptions Halfangle Accel lraf hraf mper wavenumber itime
from __future__ import annotations

import os
from ctypes import POINTER, c_bool, c_char_p, c_double, c_long, c_void_p, create_string_buffer
from typing import TYPE_CHECKING, Any

from msl.loadlib import LoadLibrary

from msl.equipment.interfaces import MSLConnectionError
from msl.equipment.schema import Interface
from msl.equipment.utils import logger

if TYPE_CHECKING:
    from ctypes import CDLL
    from typing import Any

    from msl.equipment._types import PathLike
    from msl.equipment.schema import Equipment


class PrincetonInstruments(Interface, manufacturer=r"Princeton Instruments", model=r".*"):
    """Wrapper around the `ARC_Instrument.dll` SDK from [Princeton Instruments]{:target="_blank"}.

    [Princeton Instruments]: https://www.princetoninstruments.com/
    """

    _SDK: CDLL | None = None

    def __init__(self, equipment: Equipment) -> None:
        """Wrapper around the `ARC_Instrument.dll` SDK from Princeton Instruments.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the `ARC_Instrument` wrapper.

        Attributes: Connection Properties:
            sdk_path (str): The path to the SDK library. _Default: `"ARC_Instrument_x64.dll"`_
            open (bool): Whether to automatically open the connection. _Default: `True`_
        """
        self._mono_enum: int = -1
        self._ncl_enum: int = -1
        self._filter_enum: int = -1
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        p = equipment.connection.properties

        _load_sdk(p.get("sdk_path", "ARC_Instrument_x64.dll"))
        assert self._sdk is not None  # noqa: S101

        self._sdk: CDLL = self._sdk
        if p.get("open", True):
            num_found = self.get_num_found_inst_ports()
            if num_found == 0:
                num_found = self.search_for_inst()

            for enum in range(num_found):
                port = self.get_enum_preopen_com(enum)
                if not equipment.connection.address.endswith(str(port)):
                    continue

                try:
                    self.open_mono(enum)
                except MSLConnectionError:
                    try:
                        self.open_filter(enum)
                    except MSLConnectionError:
                        try:
                            _ = self.open_readout(enum)
                        except MSLConnectionError:
                            msg = "Could not open port {port!r}"
                            raise MSLConnectionError(self, msg) from None

    def _errcheck(self, result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
        _log_errcheck(result, func, arguments)
        error_code = arguments[-1].value
        if error_code != 0:
            msg = self.error_to_english(error_code)
            raise MSLConnectionError(self, msg)
        return result

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Close all open connections."""
        if self._mono_enum > -1:
            self.close_enum(self._mono_enum)
            super().disconnect()
            self._mono_enum = -1
        if self._ncl_enum > -1:
            self.close_enum(self._ncl_enum)
            super().disconnect()
            self._ncl_enum = -1
        if self._filter_enum > -1:
            self.close_enum(self._filter_enum)
            super().disconnect()
            self._filter_enum = -1

    @staticmethod
    def close_enum(enum: int) -> None:
        """Function to close an open enumeration.

        Args:
            enum: A handle defined in *ARC_Open_xxxx* by which the instrument is to be addressed.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        if enum > -1:
            error_code = c_long()
            PrincetonInstruments._SDK.ARC_Close_Enum(enum, error_code)

    def det_read(self, det_num: int) -> float:
        """Readout a single detector.

        Args:
            det_num: The detector to be addressed.

        Returns:
            Reading value for the selected detector.
        """
        read = c_double()
        error_code = c_long()
        self._sdk.ARC_Det_Read(self._ncl_enum, det_num, read, error_code)
        return read.value

    def det_readall(self) -> tuple[float, float, float]:
        """Readout all detectors.

        Returns:
            The reading of each detector.
        """
        det1 = c_double()
        det2 = c_double()
        det3 = c_double()
        error_code = c_long()
        self._sdk.ARC_Det_ReadAll(self._ncl_enum, det1, det2, det3, error_code)
        return det1.value, det2.value, det3.value

    def det_start_nonblock_read(self, det_num: int) -> None:
        """Start to readout a single detector, but return immediately (non-blocking read).

        Args:
            det_num: The detector to be addressed.
        """
        error_code = c_long()
        self._sdk.ARC_Det_Start_NonBlock_Read(self._ncl_enum, det_num, error_code)

    def det_nonblock_read_done(self, det_num: int) -> float:
        """Returns the detector value.

        Args:
            det_num: The detector to be addressed.

        Returns:
            The value of the detector.
        """
        value = c_double()
        error_code = c_long()
        self._sdk.ARC_Det_NonBlock_Read_Done(self._ncl_enum, det_num, value, error_code)
        return value.value

    def filter_home(self) -> None:
        """Homes the filter wheel."""
        error_code = c_long()
        self._sdk.ARC_Filter_Home(self._filter_enum, error_code)

    def mono_filter_home(self) -> None:
        """Homes the filter wheel."""
        error_code = c_long()
        self._sdk.ARC_Mono_Filter_Home(self._mono_enum, error_code)

    def mono_grating_calc_gadjust(self, grating: int, wave: float, ref_wave: float) -> int:
        """Calculate a new grating GAdjust.

        Args:
            grating: The number of the grating that is to be addressed.
            wave: The wavelength, in nm, on which a peak is currently falling.
            ref_wave: The wavelength, in nm, on which the peak should fall.

        Returns:
            The calculated grating GAdjust. Note, this value is specific to a specific
                instrument-grating combination and not transferable between instruments.
        """
        new_gadjust = c_long()
        error_code = c_long()
        self._sdk.ARC_Mono_Grating_Calc_Gadjust(self._mono_enum, grating, wave, ref_wave, new_gadjust, error_code)
        return new_gadjust.value

    def mono_grating_calc_offset(self, grating: int, wave: float, ref_wave: float) -> int:
        """Calculate a new grating offset.

        Args:
            grating: The number of the grating that is to be addressed.
            wave: The wavelength, in nm, on which a peak is currently falling.
            ref_wave: The wavelength, in nm, on which the peak should fall.

        Returns:
            The calculated grating offset. Note, this value is specific to a specific
                instrument-grating combination and not transferable between instruments.
        """
        new_offset = c_long()
        error_code = c_long()
        self._sdk.ARC_Mono_Grating_Calc_Offset(self._mono_enum, grating, wave, ref_wave, new_offset, error_code)
        return new_offset.value

    def mono_grating_install(  # noqa: PLR0913
        self,
        *,
        grating: int,
        density: int,
        blaze: str,
        nm_blaze: bool,
        um_blaze: bool,
        hol_blaze: bool,
        mirror: bool,
        reboot: bool,
    ) -> None:
        """Install a new grating.

        Args:
            grating: The number of the grating that is to be addressed.
            density: The groove density in grooves per mm of the grating.
            blaze: The Blaze string.
            nm_blaze: Whether the grating has a nm blaze.
            um_blaze: Whether the grating has a um blaze.
            hol_blaze: Whether the grating has a holographic blaze.
            mirror: Whether the grating position is a mirror.
            reboot: Whether to reboot the monochromator after installing.
        """
        bb = create_string_buffer(blaze.encode())
        error_code = c_long()
        self._sdk.ARC_Mono_Grating_Install_CharStr(
            self._mono_enum, grating, density, bb, len(bb), nm_blaze, um_blaze, hol_blaze, mirror, reboot, error_code
        )

    def mono_grating_uninstall(self, grating: int, *, reboot: bool) -> None:
        """Uninstall a grating.

        Args:
            grating: The number of the grating that is to be uninstalled.
            reboot: Whether to reboot the monochromator after uninstalling.
        """
        error_code = c_long()
        self._sdk.ARC_Mono_Grating_UnInstall(self._mono_enum, grating, reboot, error_code)

    def mono_move_steps(self, num_steps: int) -> None:
        """Move the grating a set number of steps.

        Args:
            num_steps: Number of steps to move the wavelength drive.
        """
        error_code = c_long()
        self._sdk.ARC_Mono_Move_Steps(self._mono_enum, num_steps, error_code)

    def mono_reset(self) -> None:
        """Reset the monochromator."""
        error_code = c_long()
        self._sdk.ARC_Mono_Reset(self._mono_enum, error_code)

    def mono_restore_factory_settings(self) -> None:
        """Restore the instrument factory settings."""
        error_code = c_long()
        self._sdk.ARC_Mono_Restore_Factory_Settings(self._mono_enum, error_code)

    def mono_scan_done(self) -> tuple[bool, float]:
        """Check if a scan has completed.

        Returns:
            Whether the scan finished (the scan ended or the grating wavelength limit was reached) and
                the current wavelength, in nm, of the grating.
        """
        done = c_bool()
        nm = c_double()
        error_code = c_long()
        self._sdk.ARC_Mono_Scan_Done(self._mono_enum, done, nm, error_code)
        return done.value, nm.value

    def mono_slit_home(self, slit_num: int) -> None:
        """Homes a motorized slit.

        Args:
            slit_num: The slit to be homed.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        """
        error_code = c_long()
        self._sdk.ARC_Mono_Slit_Home(self._mono_enum, slit_num, error_code)

    @staticmethod
    def mono_slit_name(slit_num: int) -> str:
        """Returns a text description of a slit position.

        Args:
            slit_num: The slit to be addressed.

        Returns:
            The description of the slit port location.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        buffer = create_string_buffer(255)
        error_code = c_long()
        PrincetonInstruments._SDK.ARC_Mono_Slit_Name_CharStr(slit_num, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def mono_start_jog(self, *, jog_max_rate: bool, jog_forwards: bool) -> None:
        """Start jogging the wavelength of the monochromator.

        Args:
            jog_max_rate: Whether to jog at the max scan rate or at the current scan rate.

                * `False` &mdash; Current Scan Rate.
                * `True` &mdash; Max Scan Rate.

            jog_forwards: Whether to jog forward (increasing nm) or backwards (decreasing nm).

                * `False` &mdash; Jog Backwards (decreasing nm).
                * `True` &mdash; Jog Forwards (increasing nm).

        """
        error_code = c_long()
        self._sdk.ARC_Mono_Start_Jog(self._mono_enum, jog_max_rate, jog_forwards, error_code)

    def mono_start_scan_to_nm(self, wavelength_nm: float) -> None:
        """Start a wavelength scan.

        Args:
            wavelength_nm: Wavelength in nm we are to scan to. Note, the value should not be lower than the
                current wavelength and should not exceed the current grating wavelength limit.
        """
        error_code = c_long()
        self._sdk.ARC_Mono_Start_Scan_To_nm(self._mono_enum, wavelength_nm, error_code)

    def mono_stop_jog(self) -> None:
        """End a wavelength jog."""
        error_code = c_long()
        self._sdk.ARC_Mono_Stop_Jog(self._mono_enum, error_code)

    def calc_mono_slit_bandpass(self, slit_num: int, width: float) -> float:
        """Calculates the band pass for the provided slit width.

        Args:
            slit_num: The slit number.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

            width: The slit width that the band pass is being calculated for.

        Returns:
            The calculated band pass for the slit, in nm.
        """
        bp = c_double()
        error_code = c_long()
        self._sdk.ARC_Calc_Mono_Slit_BandPass(self._mono_enum, slit_num, width, bp, error_code)
        return bp.value

    def ncl_filter_home(self) -> None:
        """Home the filter wheel."""
        error_code = c_long()
        self._sdk.ARC_NCL_Filter_Home(self._ncl_enum, error_code)

    def open_filter(self, enum: int) -> None:
        """Function to open a filter wheel.

        Args:
            enum: Number in the enumeration list to open.
        """
        handle = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_Filter(enum, handle, error_code)
        self._filter_enum = handle.value

    def open_mono(self, enum: int) -> None:
        """Function to open a Monochromator.

        Args:
            enum: Number in the enumeration list to open.
        """
        handle = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_Mono(enum, handle, error_code)
        self._mono_enum = handle.value

    def open_mono_port(self, port: str) -> None:
        """Function to open a Monochromator on a specific COM Port.

        Args:
            port: The COM port (e.g., `"COM5"`).
        """
        handle = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_Mono_Port(int(port[3:]), handle, error_code)
        self._mono_enum = handle.value

    def open_mono_serial(self, serial: str) -> None:
        """Function to open a Monochromator with a specific serial number.

        Args:
            serial: The serial number of the Monochromator.
        """
        handle = c_long()
        model = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_Mono_Serial(int(serial), handle, model, error_code)
        self._mono_enum = handle.value

    def open_filter_port(self, port: str) -> None:
        """Function to open a filter wheel on a specific COM Port.

        Args:
            port: The COM port (e.g., `"COM5"`).
        """
        handle = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_Filter_Port(int(port[3:]), handle, error_code)
        self._filter_enum = handle.value

    def open_filter_serial(self, serial: str) -> None:
        """Function to open a filter wheel with a specific serial number.

        Args:
           serial: The serial number of the filter wheel.
        """
        handle = c_long()
        model = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_Filter_Serial(int(serial), handle, model, error_code)
        self._filter_enum = handle.value

    def open_readout(self, port: int) -> tuple[int, int]:
        """Function to open a Readout System (NCL/NCL-Lite).

        Args:
            port: Number in the enumeration list to open.

        Returns:
            The first [int][] is the enum by which to address the first mono attached to an NCL on port 1.
                The second [int][] is the enum by which to address the second mono attached to an NCL on port 2.
        """
        handle = c_long()
        mono1 = c_long()
        mono2 = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_ReadOut(port, handle, mono1, mono2, error_code)
        self._ncl_enum = handle.value
        return mono1.value, mono2.value

    def open_readout_port(self, port: str) -> tuple[int, int]:
        """Function to open a Readout System (NCL/NCL-Lite) on a specific COM Port.

        Args:
            port: The COM port (e.g., `"COM5"`).

        Returns:
            The first [int][] is the enum by which to address the first mono attached to an NCL on port 1.
                The second [int][] is the enum by which to address the second mono attached to an NCL on port 2.
        """
        handle = c_long()
        mono1 = c_long()
        mono2 = c_long()
        error_code = c_long()
        self._sdk.ARC_Open_ReadOut_Port(int(port[3:]), handle, mono1, mono2, error_code)
        self._ncl_enum = handle.value
        return mono1.value, mono2.value

    @staticmethod
    def search_for_inst() -> int:
        """Search for all attached Princeton Instruments.

        Returns:
            The number of Princeton Instruments found and enumerated.
                Enumeration list starts with zero and ends with the *number found* minus one.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        num_found = c_long()
        PrincetonInstruments._SDK.ARC_Search_For_Inst(num_found)
        return num_found.value

    def valid_det_num(self, det_num: int) -> bool:
        """Check if the detector number is valid on the Readout System.

        Args:
            det_num: The detector number to check.

        Returns:
            Whether the detector number is valid on the Readout System.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_Valid_Det_Num(self._ncl_enum, det_num, error_code))

    @staticmethod
    def valid_enum(enum: int) -> bool:
        """Check if an enumeration (handle) is valid and the instrument is open.

        Args:
            enum: The enumeration to check.

        Returns:
            Whether the enumeration is valid and the instrument is open.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        error_code = c_long()
        return bool(PrincetonInstruments._SDK.ARC_Valid_Enum(enum, error_code))

    @staticmethod
    def valid_mono_enum(mono_enum: int) -> bool:
        """Check if a monochromator enumeration (handle) is valid and the instrument is open.

        All functions call this function to verify that the requested action is valid.

        Args:
            mono_enum: The enumeration to check.

        Returns:
            Whether the enumeration is valid and the instrument is open.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        error_code = c_long()
        return bool(PrincetonInstruments._SDK.ARC_Valid_Mono_Enum(mono_enum, error_code))

    @staticmethod
    def valid_readout_enum(readout_enum: int) -> bool:
        """Check if a Readout System (NCL/NCL-Lite) enumeration (handle) is valid and the instrument is open.

        Args:
        readout_enum: The enumeration to check.

        Returns:
            Whether the enumeration is valid and the instrument is open.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        error_code = c_long()
        return bool(PrincetonInstruments._SDK.ARC_Valid_ReadOut_Enum(readout_enum, error_code))

    @staticmethod
    def valid_filter_enum(filter_enum: int) -> bool:
        """Check if a filter wheel enumeration (handle) is valid and the instrument is open.

        Args:
            filter_enum: The enumeration to check.

        Returns:
            Whether the enumeration is valid and the instrument is open.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        error_code = c_long()
        return bool(PrincetonInstruments._SDK.ARC_Valid_Filter_Enum(filter_enum, error_code))

    @staticmethod
    def ver() -> tuple[int, int, int]:
        """Get the DLL version number.

        It is the only function that can be called at any time.

        Returns:
            The `(major, minor, build)` version number.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        major = c_long()
        minor = c_long()
        build = c_long()
        if not PrincetonInstruments._SDK.ARC_Ver(major, minor, build):
            msg = "PrincetonInstrumentsError: Cannot get the DLL version number"
            raise RuntimeError(msg)

        return major.value, minor.value, build.value

    def get_det_bipolar(self, det_num: int) -> bool:
        """Return if a detector takes bipolar (+/-) readings.

        Args:
            det_num: The detector to be addressed.

        Returns:
            `True` if the detector is bipolar (+/-), `False` if unipolar.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Det_BiPolar(self._ncl_enum, det_num, error_code))

    def get_det_bipolar_str(self, det_num: int) -> str:
        """Return the description of the detector polarity.

        Args:
            det_num: The detector to be addressed.

        Returns:
            A description of whether the detector is unipolar or bipolar.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Det_BiPolar_CharStr(self._ncl_enum, det_num, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_det_hv_volts(self, det_num: int) -> int:
        """Return the high voltage volts setting.

        Args:
            det_num: The detector to be addressed.

        Returns:
            High voltage volts that the detector is set to.
        """
        error_code = c_long()
        return int(self._sdk.ARC_get_Det_HV_Volts(self._ncl_enum, det_num, error_code))

    def get_det_hv_on(self, det_num: int) -> bool:
        """Return if the high voltage for a detector is turned on.

        Args:
            det_num: The detector to be addressed.

        Returns:
            Whether the high voltage is turned on.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Det_HV_on(self._ncl_enum, det_num, error_code))

    def get_det_num_avg_read(self) -> int:
        """Return the number of readings that are averaged.

        Returns:
            Number of readings averaged into a single reading.
        """
        error_code = c_long()
        return int(self._sdk.ARC_get_Det_NumAvgRead(self._ncl_enum, error_code))

    def get_det_range(self, det_num: int) -> int:
        """Return the detector range factor.

        Args:
            det_num: The detector to be addressed.

        Returns:
            The detector gain range.

                * `0` &mdash; 1x
                * `1` &mdash; 2x
                * `2` &mdash; 4x
                * `3` &mdash; 50x
                * `4` &mdash; 200x

        """
        gain_range = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Det_Range(self._ncl_enum, det_num, gain_range, error_code)
        return gain_range.value

    def get_det_range_factor(self, det_num: int) -> int:
        """Return the detector range multiplier.

        Args:
            det_num: The detector to be addressed.

        Returns:
            The detector range multiplier.
        """
        range_factor = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Det_Range_Factor(self._ncl_enum, det_num, range_factor, error_code)
        return range_factor.value

    def get_det_type(self, det_num: int) -> int:
        """Return the detector readout type (Current, Voltage, Photon Counting).

        Args:
            det_num: The detector to be addressed.

        Returns:
            The detector readout type.

                * `1` &mdash; Current
                * `2` &mdash; Voltage
                * `3` &mdash; Photon Counting

        """
        det_type = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Det_Type(self._ncl_enum, det_num, det_type, error_code)
        return det_type.value

    def get_det_type_str(self, det_num: int) -> str:
        """Return a description of the detector readout type.

        Args:
            det_num: The detector to be addressed.

        Returns:
            The detector readout type (Current, Voltage, Photon Counting).
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Det_Type_CharStr(self._ncl_enum, det_num, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_filter_max_pos(self) -> int:
        """Returns the maximum filter position.

        Returns:
            Returns the maximum position possible with the filter wheel.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Filter_Max_Pos(self._filter_enum, position, error_code)
        return position.value

    def get_filter_min_pos(self) -> int:
        """Returns the minimum filter position.

        Returns:
            Returns the minimum position possible with the filter wheel.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Filter_Min_Pos(self._filter_enum, position, error_code)
        return position.value

    def get_filter_model(self) -> str:
        """Returns the model string from the instrument.

        Returns:
            The model string of the instrument.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Filter_Model_CharStr(self._filter_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_filter_position(self) -> int:
        """Returns the current filter position.

        Returns:
            The current filter wheel position.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Filter_Position(self._filter_enum, position, error_code)
        return position.value

    def get_filter_present(self) -> bool:
        """Returns if the instrument has a filter wheel.

        Returns:
            Whether an integrated filter wheel is present on the filter wheel.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Filter_Present(self._filter_enum, error_code))

    def get_filter_serial(self) -> str:
        """Returns the serial number of the filter wheel.

        Returns:
            The serial number of the filter wheel.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Filter_Serial_CharStr(self._filter_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    @staticmethod
    def get_filter_preopen_model(filter_enum: int) -> str:
        """Returns the model string of an instrument not yet opened.

        Note, [search_for_inst][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.search_for_inst]
        needs to be called prior to this call. In the case of multiple filter wheel/spectrographs attached, it allows
        the user to sort, which instruments are to be opened before opening them.

        Args:
            filter_enum: A filter enumeration value.

        Returns:
            The model string of the unopened filter wheel.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        buffer = create_string_buffer(255)
        error_code = c_long()
        PrincetonInstruments._SDK.ARC_get_Filter_preOpen_Model_CharStr(filter_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    @staticmethod
    def get_enum_preopen_model(enum: int) -> str:
        """Returns the model number of an instrument not yet opened.

        Note, [search_for_inst][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.search_for_inst]
        needs to be called prior to this call.

        Args:
            enum: The enumeration for the unopened instrument.

        Returns:
            The model number of the Princeton Instruments device.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        buffer = create_string_buffer(255)
        error_code = c_long()
        PrincetonInstruments._SDK.ARC_get_Enum_preOpen_Model(enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    @staticmethod
    def get_enum_preopen_serial(enum: int) -> str:
        """Returns the serial number of an instrument not yet opened.

        Note, [search_for_inst][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.search_for_inst]
        needs to be called prior to this call.

        Args:
            enum: The enumeration for the unopened instrument.

        Returns:
            The serial number of the Princeton Instruments device.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        serial = c_long()
        error_code = c_long()
        PrincetonInstruments._SDK.ARC_get_Enum_preOpen_Serial_int32(enum, serial, error_code)
        return str(serial.value)

    @staticmethod
    def get_enum_preopen_com(enum: int) -> int:
        """Returns the COM port number of an instrument not yet opened.

        Note, [search_for_inst][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.search_for_inst]
        needs to be called prior to this call.

        Args:
            enum: The enumeration for the unopened instrument.

        Returns:
            The COM port number.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        com = c_long()
        error_code = c_long()
        PrincetonInstruments._SDK.ARC_get_Enum_preOpen_COM(enum, com, error_code)
        return com.value

    def get_mono_backlash_steps(self) -> int:
        """Returns the number of backlash steps used when reversing the wavelength drive.

        Returns:
            The number of steps the instrument backlash corrects. Not valid on older instruments.
        """
        backlash = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Backlash_Steps(self._mono_enum, backlash, error_code)
        return backlash.value

    def get_mono_detector_angle(self) -> float:
        """Returns the default detector angle of the instrument in radians.

        Returns:
            The default detector angle of the instrument in radians.
        """
        angle = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_DetectorAngle(self._mono_enum, angle, error_code)
        return angle.value

    def get_mono_diverter_pos(self, diverter_num: int) -> int:
        """Returns the slit that the diverter mirror is pointing to.

        Args:
            diverter_num: The diverter to be queried.

                * `1` &mdash; Motorized entrance diverter mirror.
                * `2` &mdash; Motorized exit diverter mirror.
                * `3` &mdash; Motorized entrance diverter on a double slave unit.
                * `4` &mdash; Motorized exit diverter on a double slave unit.

        Returns:
            The slit port that the diverter mirror is currently pointing at.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        """
        diverter_pos = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Diverter_Pos(self._mono_enum, diverter_num, diverter_pos, error_code)
        return diverter_pos.value

    def get_mono_diverter_pos_str(self, diverter_num: int) -> str:
        """Returns a string describing the port the mirror is pointing to.

        Args:
            diverter_num: The diverter to be queried.

                * `1` &mdash; Motorized entrance diverter mirror.
                * `2` &mdash; Motorized exit diverter mirror.
                * `3` &mdash; Motorized entrance diverter on a double slave unit.
                * `4` &mdash; Motorized exit diverter on a double slave unit.

        Returns:
            A string describing which port the diverter is pointing at.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Mono_Diverter_Pos_CharStr(self._mono_enum, diverter_num, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_mono_diverter_valid(self, diverter_num: int) -> bool:
        """Returns if a motorized diverter position is valid for an instrument.

        Args:
            diverter_num: The diverter to be queried.

                * `1` &mdash; Motorized entrance diverter mirror.
                * `2` &mdash; Motorized exit diverter mirror.
                * `3` &mdash; Motorized entrance diverter on a double slave unit.
                * `4` &mdash; Motorized exit diverter on a double slave unit.

        Returns:
            Whether the diverter mirror is valid.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Diverter_Valid(self._mono_enum, diverter_num, error_code))

    def get_mono_double(self) -> bool:
        """Returns if the instrument is a double monochromator.

        Returns:
            Whether the instrument is a double monochromator.
        """
        double_present = c_bool()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Double(self._mono_enum, double_present, error_code)
        return double_present.value

    def get_mono_double_subtractive(self) -> bool:
        """Returns if a double monochromator is subtractive instead of additive.

        Returns:
            Whether the double monochromator is subtractive.
        """
        double_subtractive = c_bool()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Double_Subtractive(self._mono_enum, double_subtractive, error_code)
        return double_subtractive.value

    def get_mono_double_intermediate_slit(self) -> int:
        """If a monochromator is a double, return the intermediate slit position.

        Returns:
            The intermediate slit of the double monochromator

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        """
        slit_pos = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Double_Intermediate_Slit(self._mono_enum, slit_pos, error_code)
        return slit_pos.value

    def get_mono_exit_slit(self) -> int:
        """Return the exit slit position for a monochromator.

        Function works with a single and double monochromator.

        Returns:
            The intermediate slit of the double monochromator

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        """
        slit_pos = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Exit_Slit(self._mono_enum, slit_pos, error_code)
        return slit_pos.value

    def get_mono_filter_max_pos(self) -> int:
        """Returns the maximum filter position.

        Returns:
            The maximum position possible with the filter wheel.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Filter_Max_Pos(self._mono_enum, position, error_code)
        return position.value

    def get_mono_filter_min_pos(self) -> int:
        """Returns the minimum filter position.

        Returns:
            The minimum position possible with the filter wheel.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Filter_Min_Pos(self._mono_enum, position, error_code)
        return position.value

    def get_mono_filter_position(self) -> int:
        """Returns the current filter position.

        Returns:
            The current filter wheel position.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Filter_Position(self._mono_enum, position, error_code)
        return position.value

    def get_mono_filter_present(self) -> bool:
        """Returns if the instrument has an integrated filter wheel.

        Note, is a new option and not available on most instruments. All filter
        functions call this function before proceeding.

        Returns:
            Whether an integrated filter wheel is present on the monochromator.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Filter_Present(self._mono_enum, error_code))

    def get_mono_focal_length(self) -> float:
        """Returns the default focal length of the instrument.

        Returns:
            The focal length of the instrument in millimetres.
        """
        focal_length = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Focallength(self._mono_enum, focal_length, error_code)
        return focal_length.value

    def get_mono_gear_steps(self) -> tuple[int, int]:
        """Returns the number of steps in a set of sine drive gears.

        Returns:
            The number of steps per rev on the `(minor, major)` gear of a sine wavelength drive.
        """
        minor = c_long()
        major = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Gear_Steps(self._mono_enum, minor, major, error_code)
        return minor.value, major.value

    def get_mono_grating(self) -> int:
        """Returns the current grating.

        Returns:
            The current grating. This assumes the correct turret has been inserted in the instrument.
        """
        grating = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Grating(self._mono_enum, grating, error_code)
        return grating.value

    def get_mono_grating_blaze(self, grating: int) -> str:
        """Returns the blaze of a given grating.

        Args:
            grating: Which grating to request the information about. Validates the request by calling
                [get_mono_grating_installed][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.get_mono_grating_installed].

        Returns:
            The blaze of the grating.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Mono_Grating_Blaze_CharStr(self._mono_enum, grating, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_mono_grating_density(self, grating: int) -> int:
        """Returns the groove density (grooves per millimetre) of a given grating.

        Args:
            grating: Which grating to request the information about. Validates the request by calling
                [get_mono_grating_installed][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.get_mono_grating_installed].

        Returns:
            The groove density of the grating in grooves per millimetre. For a mirror,
                this function will return 1200 grooves per millimetre.
        """
        groove_mm = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Grating_Density(self._mono_enum, grating, groove_mm, error_code)
        return groove_mm.value

    def get_mono_grating_gadjust(self, grating: int) -> int:
        """Returns the GAdjust of a grating.

        Args:
            grating: Which grating to request the information about.

        Returns:
            The grating GAdjust. Note, this value is specific to a specific instrument
                grating combination and not transferable between instruments.
        """
        g_adjust = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Grating_Gadjust(self._mono_enum, grating, g_adjust, error_code)
        return g_adjust.value

    def get_mono_grating_installed(self, grating: int) -> bool:
        """Returns if a grating is installed.

        Args:
            grating: Which grating we are requesting the information about.

        Returns:
            Whether the grating requested is installed.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Grating_Installed(self._mono_enum, grating, error_code))

    def get_mono_grating_max(self) -> int:
        """Get the maximum grating position installed.

        This is usually the number of gratings installed.

        Returns:
            The number of gratings installed.
        """
        num = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Grating_Max(self._mono_enum, num, error_code)
        return num.value

    def get_mono_grating_offset(self, grating: int) -> int:
        """Returns the offset of a grating.

        Args:
            grating: The number of the grating that is to be addressed.

        Returns:
            The grating offset. Note, this value is specific to a specific instrument
                grating combination and not transferable between instruments.
        """
        offset = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Grating_Offset(self._mono_enum, grating, offset, error_code)
        return offset.value

    def get_mono_half_angle(self) -> float:
        """Returns the default half angle of the instrument in radians.

        Returns:
            The half angle of the instrument in radians.
        """
        half_angle = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_HalfAngle(self._mono_enum, half_angle, error_code)
        return half_angle.value

    def get_mono_init_grating(self) -> int:
        """Returns the initial grating (on instrument reboot).

        Returns:
            The power-up grating number.
        """
        init_grating = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Init_Grating(self._mono_enum, init_grating, error_code)
        return init_grating.value

    def get_mono_init_scan_rate_nm(self) -> float:
        """Returns the initial wavelength scan rate (on instrument reboot).

        Returns:
            The power-up scan rate in nm / minute.
        """
        init_scan_rate = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Init_ScanRate_nm(self._mono_enum, init_scan_rate, error_code)
        return init_scan_rate.value

    def get_mono_init_wave_nm(self) -> float:
        """Returns the initial wavelength (on instrument reboot).

        Returns:
            The power-up wavelength in nm.
        """
        init_wave = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Init_Wave_nm(self._mono_enum, init_wave, error_code)
        return init_wave.value

    def get_mono_int_led_on(self) -> bool:
        """Checks if the interrupter LED is on.

        Returns:
            Whether the interrupter LED is on.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Int_Led_On(self._mono_enum, error_code))

    def get_mono_model(self) -> str:
        """Returns the model number of the monochromator.

        Returns:
            The model number of the monochromator.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Mono_Model_CharStr(self._mono_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_mono_motor_int(self) -> bool:
        """Read the motor gear interrupter.

        Returns:
            Whether the motor gear was interrupted.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Motor_Int(self._mono_enum, error_code))

    def get_mono_precision(self) -> int:
        """Returns the nm-decimal precision of the wavelength drive.

        Note, this is independent of the wavelength step resolution whose coarseness
        is defined by the grating being used.

        Returns:
            The number of digits after the decimal point the instrument uses.
                Note, the true precision is limited by the density of the grating and can
                be much less than the instruments wavelength precision.
        """
        error_code = c_long()
        return int(self._sdk.ARC_get_Mono_Precision(self._mono_enum, error_code))

    def get_mono_scan_rate_nm_min(self) -> float:
        """Return the current wavelength scan rate.

        Returns:
            Scan rate in nm per minute.
        """
        scan_rate = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Scan_Rate_nm_min(self._mono_enum, scan_rate, error_code)
        return scan_rate.value

    def get_mono_serial(self) -> str:
        """Returns the serial number of the instrument.

        Returns:
            The serial number of the instrument as a string.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Mono_Serial_CharStr(self._mono_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_mono_shutter_open(self) -> bool:
        """Returns if the integrated shutter is open.

        Returns:
            Whether the shutter is open.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Shutter_Open(self._mono_enum, error_code))

    def get_mono_shutter_valid(self) -> bool:
        """Returns if the instrument has an integrated shutter.

        Returns:
            Whether a shutter is present.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Shutter_Valid(self._mono_enum, error_code))

    def get_mono_sine_drive(self) -> bool:
        """Returns if the gearing system has sine instead of a linear drive system.

        Returns:
            Whether the gearing is sine based verses linear gearing.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Sine_Drive(self._mono_enum, error_code))

    def get_mono_slit_type(self, slit_pos: int) -> int:
        """Returns the slit type for a given slit.

        Args:
            slit_pos: The slit to be addressed.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        Returns:
            The type of slit attached.

                * `0` &mdash; No slit, older instruments that do will only return a slit type of zero.
                * `1` &mdash; Manual Slit.
                * `2` &mdash; Fixed Slit Width.
                * `3` &mdash; Focal Plane adapter.
                * `4` &mdash; Continuous Motor.
                * `5` &mdash; Fibre Optic.
                * `6` &mdash; Index able Slit.

        """
        slit_type = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Slit_Type(self._mono_enum, slit_pos, slit_type, error_code)
        return slit_type.value

    def get_mono_slit_type_str(self, slit_pos: int) -> str:
        """Returns a string descriptor of a given slit.

        Args:
            slit_pos: The slit to be addressed.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        Returns:
            The description of the slit.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_Mono_Slit_Type_CharStr(self._mono_enum, slit_pos, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_mono_slit_width(self, slit_pos: int) -> int:
        """Returns the slit width of a motorized slit.

        Args:
            slit_pos: The slit to be addressed.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        Returns:
            The width of the slit, if the slit is motorized.
        """
        slit_width = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Slit_Width(self._mono_enum, slit_pos, slit_width, error_code)
        return slit_width.value

    def get_mono_slit_width_max(self, slit_pos: int) -> int:
        """Returns the maximum width of a motorized slit.

        Args:
            slit_pos: The slit to be addressed.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        Returns:
            The maximum width of the slit, if the slit is motorized.
        """
        slit_width = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Slit_Max(self._mono_enum, slit_pos, slit_width, error_code)
        return slit_width.value

    def get_mono_turret(self) -> int:
        """Returns the current grating turret number.

        Returns:
            The current turret number.
        """
        turret = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Turret(self._mono_enum, turret, error_code)
        return turret.value

    def get_mono_turret_max(self) -> int:
        """Returns the number of turrets installed.

        Returns:
            The number of turrets installed.
        """
        turret = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Turret_Max(self._mono_enum, turret, error_code)
        return turret.value

    def get_mono_turret_gratings(self) -> int:
        """Returns the number of gratings per turret.

        Returns:
            The number of gratings that can be placed on a single turret. This number can be one,
                two or three depending on the monochromator model.
        """
        gratings_per_turret = c_long()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Turret_Gratings(self._mono_enum, gratings_per_turret, error_code)
        return gratings_per_turret.value

    def get_mono_wavelength_cutoff_nm(self) -> float:
        """Returns, in nm, the max wavelength achievable by the instrument using the current grating.

        Returns:
            The maximum center wavelength in nanometres for the current grating.
                On SpectraPro's this value equals 1400 nm * grating density / 1200 g/mm.
                On AM/VM products, this value is limited by the sine bar and will vary.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_Cutoff_nm(self._mono_enum, wavelength, error_code)
        return wavelength.value

    def get_mono_wavelength_min_nm(self) -> float:
        """Returns, in nm, the min wavelength achievable by the instrument using the current grating.

        Returns:
            The minimum center wavelength in nanometres for the current grating.
                On SpectraPro's it is usually -10 nm, on linear AM/VM instruments this value will vary.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_Min_nm(self._mono_enum, wavelength, error_code)
        return wavelength.value

    def get_mono_wavelength_abs_cm(self) -> float:
        """Returns the current center wavelength of instrument in absolute wavenumber.

        Returns:
            The current wavelength of the instrument in absolute wavenumber.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_absCM(self._mono_enum, wavelength, error_code)
        return wavelength.value

    def get_mono_wavelength_ang(self) -> float:
        """Returns the current center wavelength of instrument in Angstroms.

        Returns:
            The current wavelength of the instrument in Angstroms.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_ang(self._mono_enum, wavelength, error_code)
        return wavelength.value

    def get_mono_wavelength_ev(self) -> float:
        """Returns the current center wavelength of instrument in electron volts.

        Returns:
            The current wavelength of the instrument in electron volts.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_eV(self._mono_enum, wavelength, error_code)
        return wavelength.value

    def get_mono_wavelength_micron(self) -> float:
        """Returns the current center wavelength of instrument in microns.

        Returns:
            The current wavelength of the instrument in microns.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_micron(self._mono_enum, wavelength, error_code)
        return wavelength.value

    def get_mono_wavelength_nm(self) -> float:
        """Returns the current center wavelength of instrument in nm.

        Returns:
            The current wavelength of the instrument.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_nm(self._mono_enum, wavelength, error_code)
        return wavelength.value

    def get_mono_wavelength_rel_cm(self, center_nm: int) -> float:
        """Returns the current center wavelength of instrument in relative wavenumber.

        Args:
            center_nm: The wavelength, in nm, that the relative wavenumber is centred around.

        Returns:
            The current wavelength of the instrument in relative wavenumber.
        """
        wavelength = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_Wavelength_relCM(self._mono_enum, center_nm, wavelength, error_code)
        return wavelength.value

    def get_mono_wheel_int(self) -> bool:
        """Read the wheel gear interrupter.

        Returns:
            Whether the wheel gear was interrupted.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_Mono_Wheel_Int(self._mono_enum, error_code))

    def get_mono_nm_rev_ratio(self) -> float:
        """Returns the number of stepper steps per rev of the wavelength drive motor.

        Returns:
            The ratio of nm per rev in a linear wavelength drive.
        """
        ratio = c_double()
        error_code = c_long()
        self._sdk.ARC_get_Mono_nmRev_Ratio(self._mono_enum, ratio, error_code)
        return ratio.value

    @staticmethod
    def get_mono_preopen_model(mono_enum: int) -> str:
        """Returns the model of an instrument not yet opened.

        Note, [search_for_inst][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.search_for_inst]
        needs to be called prior to this call. In the case of multiple Monochromator/Spectrographs attached, it allows
        the user to sort, which instruments are to be opened before opening them.

        Args:
            mono_enum: A monochromator enumeration.

        Returns:
            The model of the unopened monochromator.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        buffer = create_string_buffer(255)
        error_code = c_long()
        PrincetonInstruments._SDK.ARC_get_Mono_preOpen_Model_CharStr(mono_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_ncl_filter_max_pos(self) -> int:
        """Returns the maximum filter position.

        Returns:
            The maximum filter position.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_NCL_Filter_Max_Pos(self._ncl_enum, position, error_code)
        return position.value

    def get_ncl_filter_min_pos(self) -> int:
        """Returns the minimum filter position.

        Returns:
            The minimum filter position.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_NCL_Filter_Min_Pos(self._ncl_enum, position, error_code)
        return position.value

    def get_ncl_filter_position(self) -> int:
        """Return the current filter position.

        Returns:
            The current filter position.
        """
        position = c_long()
        error_code = c_long()
        self._sdk.ARC_get_NCL_Filter_Position(self._ncl_enum, position, error_code)
        return position.value

    def get_ncl_filter_present(self) -> bool:
        """Returns if the instrument has an integrated filter wheel setup.

        Returns:
            Whether a NCL filter wheel is setup and present.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_NCL_Filter_Present(self._ncl_enum, error_code))

    def get_ncl_mono_enum(self, mono_num: int) -> int:
        """Return the enumeration of the attached monochromator.

        Args:
            mono_num: The readout system monochromator port being addressed.

        Returns:
            The enumeration of the monochromator. Check the value returned with
                [valid_mono_enum][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.valid_mono_enum].
        """
        error_code = c_long()
        return int(self._sdk.ARC_get_NCL_Mono_Enum(self._ncl_enum, mono_num, error_code))

    def get_ncl_mono_setup(self, mono_num: int) -> bool:
        """Return if the open NCL port has a Monochromator attached.

        Args:
            mono_num: The readout system monochromator port being addressed.

        Returns:
            Whether a monochromator is attached to the port and it is set up.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_NCL_Mono_Setup(self._ncl_enum, mono_num, error_code))

    def get_ncl_shutter_open(self, shutter_num: int) -> bool:
        """Return if an NCL Readout shutter is open.

        Args:
            shutter_num: The shutter being addressed (1 or 2 on an NCL).

        Returns:
            Whether the shutter is in the open position.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_NCL_Shutter_Open(self._ncl_enum, shutter_num, error_code))

    def get_ncl_shutter_valid(self, shutter_num: int) -> bool:
        """Return if a NCL Readout shutter number is valid.

        Args:
            shutter_num: The shutter being addressed (1 or 2 on an NCL).

        Returns:
            Whether the shutter number is valid.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_NCL_Shutter_Valid(self._ncl_enum, shutter_num, error_code))

    def get_ncl_ttl_in(self, ttl_line: int) -> bool:
        """Return if an input TTL line is being pulled on by an outside connection.

        Args:
            ttl_line: The TTL line number being addressed.

        Returns:
            Whether `ttl_line` is being pulled to TTL high.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_NCL_TTL_In(self._ncl_enum, ttl_line, error_code))

    def get_ncl_ttl_out(self, ttl_line: int) -> bool:
        """Return if an output TTL line is on.

        Args:
            ttl_line: The TTL line number being addressed.

        Returns:
            Whether the output `ttl_line` is set to TTL high.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_NCL_TTL_Out(self._ncl_enum, ttl_line, error_code))

    def get_ncl_ttl_valid(self, ttl_line: int) -> bool:
        """Return if a TTL line is a valid line.

        Args:
            ttl_line: The TTL line number being addressed.

        Returns:
            Whether `ttl_line` is a valid line number.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_get_NCL_TTL_Valid(self._ncl_enum, ttl_line, error_code))

    def get_num_det(self) -> int:
        """Return the number of single point detectors in the Readout System.

        Returns:
            Number of single point detectors the readout system supports. (1 NCL-Lite, 2,3 NCL).
        """
        error_code = c_long()
        return int(self._sdk.ARC_get_Num_Det(self._ncl_enum, error_code))

    @staticmethod
    def get_num_found_inst_ports() -> int:
        """Returns the value last returned by [search_for_inst][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.search_for_inst].

        Can be called multiple times.

        Returns:
            The number of instruments found.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        return int(PrincetonInstruments._SDK.ARC_get_Num_Found_Inst_Ports())

    def get_readout_itime_ms(self) -> int:
        """Return the integration time used for taking a reading.

        Returns:
            The integration time used for taking a reading, in milliseconds.
        """
        error_code = c_long()
        return int(self._sdk.ARC_get_ReadOut_ITime_ms(self._ncl_enum, error_code))

    def get_readout_model(self) -> str:
        """Returns the model string from the instrument.

        Returns:
            The model string of the instrument.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_ReadOut_Model_CharStr(self._ncl_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def get_readout_serial(self) -> str:
        """Returns the serial number from the instrument.

        Returns:
            The serial number of the instrument as a string.
        """
        buffer = create_string_buffer(255)
        error_code = c_long()
        self._sdk.ARC_get_ReadOut_Serial_CharStr(self._ncl_enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    @staticmethod
    def get_readout_preopen_model(enum: int) -> str:
        """Returns the model string of an instrument not yet opened.

        Note, [search_for_inst][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.search_for_inst]
        needs to be called prior to this call. In the case of multiple Readout Systems attached, it allows the user
        to sort, which instruments are to be opened before opening them.

        Args:
            enum: The instrument enumeration.

        Returns:
            The model string of the unopened instrument.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        buffer = create_string_buffer(255)
        error_code = c_long()
        PrincetonInstruments._SDK.ARC_get_ReadOut_preOpen_Model_CharStr(enum, buffer, len(buffer), error_code)
        return bytes(buffer.value).decode()

    def set_det_bipolar(self, det_num: int) -> None:
        """Set the detector readout to bipolar (+/-).

        Args:
            det_num: The detector to be addressed.
        """
        error_code = c_long()
        self._sdk.ARC_set_Det_BiPolar(self._ncl_enum, det_num, error_code)

    def set_det_current(self, det_num: int) -> None:
        """Set the detector readout type to Current.

        Args:
            det_num: The detector to be addressed.
        """
        error_code = c_long()
        self._sdk.ARC_set_Det_Current(self._ncl_enum, det_num, error_code)

    def set_det_hv_volts(self, det_num: int, hv_volts: int) -> None:
        """Set the value of the high voltage.

        Args:
            det_num: The detector to be addressed.
            hv_volts: The high-voltage value.
        """
        error_code = c_long()
        self._sdk.ARC_set_Det_HV_Volts(self._ncl_enum, det_num, hv_volts, error_code)

    def set_det_hv_off(self, det_num: int) -> bool:
        """Set the detector high voltage to off.

        Args:
            det_num: The detector to be addressed.

        Returns:
            Whether the high voltage has been turned off.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_set_Det_HV_off(self._ncl_enum, det_num, error_code))

    def set_det_hv_on(self, det_num: int) -> bool:
        """Set the detector high voltage to on.

        Args:
            det_num: The detector to be addressed.

        Returns:
            Whether the high voltage has been turned on.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_set_Det_HV_on(self._ncl_enum, det_num, error_code))

    def set_det_num_avg_read(self, num_reads_avg: int) -> None:
        """Set the number of readings to average.

        Args:
            num_reads_avg: The number reads that will be required to acquire a single read.
        """
        error_code = c_long()
        self._sdk.ARC_set_Det_NumAvgRead(self._ncl_enum, num_reads_avg, error_code)

    def set_det_photon(self, det_num: int) -> None:
        """Set the detector readout type to Photon Counter.

        Args:
            det_num: The detector to be addressed.
        """
        error_code = c_long()
        self._sdk.ARC_set_Det_Photon(self._ncl_enum, det_num, error_code)

    def set_det_range(self, det_num: int, gain_range: int) -> None:
        """Set the detector gain-range factor.

        Args:
            det_num: The detector to be addressed.
            gain_range: The detector gain range.

                * `0` &mdash; 1x
                * `1` &mdash; 2x
                * `2` &mdash; 4x
                * `3` &mdash; 50x
                * `4` &mdash; 200x

        """
        error_code = c_long()
        self._sdk.ARC_set_Det_Range(self._ncl_enum, det_num, gain_range, error_code)

    def set_det_type(self, det_num: int, det_type: int) -> None:
        """Set the detector readout type.

        Args:
            det_num: The detector to be addressed.
            det_type: The detector readout type.

                * `1` &mdash; Current
                * `2` &mdash; Voltage
                * `3` &mdash; Photon Counting

        """
        error_code = c_long()
        self._sdk.ARC_set_Det_Type(self._ncl_enum, det_num, det_type, error_code)

    def set_det_unipolar(self, det_num: int) -> None:
        """Set the detector readout to unipolar (-).

        Args:
            det_num: The detector to be addressed.
        """
        error_code = c_long()
        self._sdk.ARC_set_Det_UniPolar(self._ncl_enum, det_num, error_code)

    def set_det_voltage(self, det_num: int) -> None:
        """Set the detector readout type to voltage.

        Args:
            det_num: The detector to be addressed.
        """
        error_code = c_long()
        self._sdk.ARC_set_Det_Voltage(self._ncl_enum, det_num, error_code)

    def set_filter_position(self, position: int) -> None:
        """Sets the current filter position.

        Args:
            position: Position the filter is to be set to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Filter_Position(self._filter_enum, position, error_code)

    def set_mono_diverter_pos(self, diverter_num: int, diverter_pos: int) -> None:
        """Sets the port that the unit is to point to.

        Args:
            diverter_num: The diverter to be modified.

                * `1` &mdash; Motorized entrance diverter mirror.
                * `2` &mdash; Motorized exit diverter mirror.
                * `3` &mdash; Motorized entrance diverter on a double slave unit.
                * `4` &mdash; Motorized exit diverter on a double slave unit.

            diverter_pos: The slit port that the diverter mirror is to be set to. Not all ports are valid
                for all diverter's.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Diverter_Pos(self._mono_enum, diverter_num, diverter_pos, error_code)

    def set_mono_filter_position(self, position: int) -> None:
        """Sets the current filter position.

        Args:
            position: Position the filter is to be set to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Filter_Position(self._mono_enum, position, error_code)

    def set_mono_grating(self, grating: int) -> None:
        """Sets the current grating.

        Args:
            grating: Set the current grating. This assumes the correct turret is inserted in the
                instrument and grating selected is a valid grating. This function will change to
                current turret in the firmware, but needs user interaction to install the correct turret.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Grating(self._mono_enum, grating, error_code)

    def set_mono_grating_gadjust(self, grating: int, gadjust: int) -> None:
        """Sets the grating GAdjust.

        Args:
            grating: The number of the grating that is to be addressed.
            gadjust: The grating GAdjust. Note, this value is specific to a specific
                instrument-grating combination and not transferable between instruments.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Grating_Gadjust(self._mono_enum, grating, gadjust, error_code)

    def set_mono_grating_offset(self, grating: int, offset: int) -> None:
        """Sets the grating offset.

        Args:
            grating: The number of the grating that is to be addressed.
            offset: The grating offset. Note, this value is specific to a specific
                instrument-grating combination and not transferable between instruments.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Grating_Offset(self._mono_enum, grating, offset, error_code)

    def set_mono_init_grating(self, init_grating: int) -> None:
        """Sets the initial grating (on instrument reboot).

        Args:
            init_grating: The power-up grating number.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Init_Grating(self._mono_enum, init_grating, error_code)

    def set_mono_init_scan_rate_nm(self, init_scan_rate: float) -> None:
        """Sets the initial wavelength scan rate (on instrument reboot).

        Args:
            init_scan_rate: The power-up scan rate in nm / minute.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Init_ScanRate_nm(self._mono_enum, init_scan_rate, error_code)

    def set_mono_init_wave_nm(self, init_wave: float) -> None:
        """Sets the initial wavelength (on instrument reboot).

        Args:
            init_wave: The power-up wavelength in nm.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Init_Wave_nm(self._mono_enum, init_wave, error_code)

    def set_mono_int_led(self, *, enable: bool) -> None:
        """Turns on and off the interrupter LED.

        Args:
            enable: Indicates whether the LED should be on or off.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Int_Led(self._mono_enum, bool(enable), error_code)

    def set_mono_scan_rate_nm_min(self, scan_rate: float) -> None:
        """Set the wavelength scan rate.

        Args:
            scan_rate: The rate to scan the wavelength in nm/minute.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Scan_Rate_nm_min(self._mono_enum, scan_rate, error_code)

    def set_mono_shutter_closed(self) -> bool:
        """Sets the integrated shutter position to closed.

        Returns:
            Whether the shutter has been closed.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_set_Mono_Shutter_Closed(self._mono_enum, error_code))

    def set_mono_shutter_open(self) -> bool:
        """Sets the integrated shutter position to open.

        Returns:
            Whether the shutter has been opened.
        """
        error_code = c_long()
        return bool(self._sdk.ARC_set_Mono_Shutter_Open(self._mono_enum, error_code))

    def set_mono_slit_width(self, slit_pos: int, slit_width: int) -> None:
        """Sets the slit width of a motorized slit (Types 4, 6 and 9).

        Args:
            slit_pos: The slit to be addressed.

                * `1` &mdash; Side entrance slit.
                * `2` &mdash; Front entrance slit.
                * `3` &mdash; Front exit slit.
                * `4` &mdash; Side exit slit.
                * `5` &mdash; Side entrance slit on a double slave unit.
                * `6` &mdash; Front entrance slit on a double slave unit.
                * `7` &mdash; Front exit slit on a double slave unit.
                * `8` &mdash; Side exit slit on a double slave unit.

            slit_width: The width to which the slit is to be set to. Note valid ranges are
                10 to 3000 microns in one-micron increments for normal continuous
                motor slits (type 4 and 9), 10 to 12000 microns in five-micron
                increments for large continuous motor slits (type 4) and
                25, 50, 100, 250, 500, 1000 microns for indexable slits (Type 6).
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Slit_Width(self._mono_enum, slit_pos, slit_width, error_code)

    def set_mono_turret(self, turret: int) -> None:
        """Sets the current grating turret.

        Args:
            turret: Set the current turret. This will change the grating to Turret number
                minus one times gratings per turret plus the one plus the current grating
                number minus one mod gratings per turret. The user must insert the correct
                turret into the instrument when using this function.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Turret(self._mono_enum, turret, error_code)

    def set_mono_wavelength_abs_cm(self, wavelength: float) -> None:
        """Sets the center wavelength of the instrument in absolute wavenumber's.

        Args:
            wavelength: The wavelength in absolute wavenumber that the instrument is to be moved to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Wavelength_absCM(self._mono_enum, wavelength, error_code)

    def set_mono_wavelength_ang(self, wavelength: float) -> None:
        """Sets the center wavelength of the instrument in angstroms.

        Args:
            wavelength: The wavelength in Angstroms that the instrument is to be moved to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Wavelength_ang(self._mono_enum, wavelength, error_code)

    def set_mono_wavelength_ev(self, wavelength: float) -> None:
        """Sets the center wavelength of the instrument in Electron Volts.

        Args:
            wavelength: The wavelength in Electron Volts that the instrument is to be moved to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Wavelength_eV(self._mono_enum, wavelength, error_code)

    def set_mono_wavelength_micron(self, wavelength: float) -> None:
        """Sets the center wavelength of the instrument in microns.

        Args:
            wavelength: The wavelength in microns that the instrument is to be moved to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Wavelength_micron(self._mono_enum, wavelength, error_code)

    def set_mono_wavelength_nm(self, wavelength: float) -> None:
        """Sets the center wavelength of the instrument in nm.

        Args:
            wavelength: The wavelength in nm that the instrument is to be moved to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Wavelength_nm(self._mono_enum, wavelength, error_code)

    def set_mono_wavelength_rel_cm(self, center_nm: float, wavelength: float) -> None:
        """Sets the center wavelength of the instrument in relative wavenumber's.

        Args:
            center_nm: The wavelength in nanometres that 0 relative Wavenumber is centred around.
            wavelength: The wavelength in relative Wavenumber that the instrument is to be moved to.
        """
        error_code = c_long()
        self._sdk.ARC_set_Mono_Wavelength_relCM(self._mono_enum, center_nm, wavelength, error_code)

    def set_ncl_filter_position(self, position: int) -> None:
        """Set the current filter position.

        Args:
            position: The current filter position.
        """
        error_code = c_long()
        self._sdk.ARC_set_NCL_Filter_Position(self._ncl_enum, position, error_code)

    def set_ncl_filter_present(self, min_filter: int, max_filter: int) -> None:
        """Set the instrument filter wheel to active (NCL only).

        Args:
            min_filter: Minimum filter position (on an NCL with the standard filter wheel 1).
            max_filter: Maximum filter position (on an NCL with the standard filter wheel 6).
        """
        error_code = c_long()
        self._sdk.ARC_set_NCL_Filter_Present(self._ncl_enum, min_filter, max_filter, error_code)

    def set_ncl_shutter_closed(self, shutter_num: int) -> None:
        """Set a NCL Readout shutter to a closed state.

        Args:
            shutter_num: The shutter being addressed (1 or 2 on an NCL).
        """
        error_code = c_long()
        self._sdk.ARC_set_NCL_Shutter_Closed(self._ncl_enum, shutter_num, error_code)

    def set_ncl_shutter_open(self, shutter_num: int) -> None:
        """Set a NCL Readout shutter to a closed state.

        Args:
            shutter_num: The shutter being addressed (1 or 2 on an NCL).
        """
        error_code = c_long()
        self._sdk.ARC_set_NCL_Shutter_Open(self._ncl_enum, shutter_num, error_code)

    def set_ncl_ttl_out_off(self, ttl_line: int) -> None:
        """Turn a TTL line off.

        Args:
            ttl_line: The TTL line number being addressed.
        """
        error_code = c_long()
        self._sdk.ARC_set_NCL_TTL_Out_Off(self._ncl_enum, ttl_line, error_code)

    def set_ncl_ttl_out_on(self, ttl_line: int) -> None:
        """Turn a TTL line on.

        Args:
            ttl_line: The TTL line number being addressed.
        """
        error_code = c_long()
        self._sdk.ARC_set_NCL_TTL_Out_On(self._ncl_enum, ttl_line, error_code)

    def set_readout_itime_ms(self, itime_ms: int) -> None:
        """Set the integration time used for taking a reading.

        Args:
            itime_ms: The integration time in milliseconds to be used when reading out a detector.
        """
        error_code = c_long()
        self._sdk.ARC_set_ReadOut_ITime_ms(self._ncl_enum, itime_ms, error_code)

    @staticmethod
    def init(path: PathLike = "ARC_Instrument_x64.dll") -> None:
        """Initialize the SDK.

        Args:
            path: The path to the SDK.
        """
        _load_sdk(os.fsdecode(path))

    @staticmethod
    def is_inited() -> bool:
        """Check if the [init][msl.equipment_resources.princeton_instruments.arc_instrument.PrincetonInstruments.init] method was called.

        Returns:
            Whether the method was called.
        """  # noqa: E501
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        return bool(PrincetonInstruments._SDK.ARC_IsInited())

    @staticmethod
    def error_to_english(error_code: int) -> str:
        """Convert an error code into a message.

        Args:
            error_code: An error code from the `ARC_Instrument` SDK.

        Returns:
            The error message.
        """
        if PrincetonInstruments._SDK is None:
            msg = "PrincetonInstrumentsError: You must first call PrincetonInstruments.init()"
            raise RuntimeError(msg)

        buffer = create_string_buffer(255)
        PrincetonInstruments._SDK.ARC_Error_To_English(error_code, buffer, len(buffer))
        return buffer.value.decode()


def _log_errcheck(result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
    logger.debug("PrincetonInstruments.%s%s -> %s", func.__name__, arguments, result)
    return result


def __errcheck(result: Any, func: Any, arguments: tuple[Any, ...]) -> Any:  # noqa: ANN401
    _log_errcheck(result, func, arguments)
    error_code = arguments[-1].value
    if error_code != 0:
        raise RuntimeError(PrincetonInstruments.error_to_english(error_code))
    return result


def _load_sdk(path: str, pi: PrincetonInstruments | None = None) -> None:
    """Load the SDK.

    Args:
        path: The path to `ARC_Instrument` SDK.
        pi: The PrincetonInstruments class instance that the SDK is associated with.
    """
    if PrincetonInstruments._SDK is not None:  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        return

    _errcheck = __errcheck if pi is None else pi._errcheck  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    functions = {  # pyright: ignore[reportUnknownVariableType]
        "ARC_Init": (c_bool, _log_errcheck, []),
        "ARC_IsInited": (c_bool, _log_errcheck, []),
        "ARC_Ver": (
            c_bool,
            _log_errcheck,
            [("Major", POINTER(c_long)), ("Minor", POINTER(c_long)), ("Build", POINTER(c_long))],
        ),
        "ARC_Error_To_English": (
            None,
            _log_errcheck,
            [("Error_Code", c_long), ("Error_Str", c_char_p), ("Error_Str_sz", c_long)],
        ),
        "ARC_Search_For_Inst": (c_bool, _log_errcheck, [("Num_Found", POINTER(c_long))]),
        "ARC_get_Num_Found_Inst_Ports": (c_long, _log_errcheck, []),
        "ARC_get_Enum_preOpen_Model": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("Model_Str", c_char_p), ("Model_Str_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Enum_preOpen_Model_int32": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("Model_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Enum_preOpen_Serial_int32": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("Serial_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Enum_preOpen_COM": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Enum_Model": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("Model_Str", c_char_p), ("Model_Str_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Enum_Model_int32": (c_long, _errcheck, [("Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Enum_Serial": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("Serial_Str", c_char_p), ("Serial_Str_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Enum_Serial_int32": (c_long, _errcheck, [("Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Enum_COM": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_Mono": (
            c_bool,
            _errcheck,
            [("Enum_Num", c_long), ("Mono_Enum", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_Mono_Port": (
            c_bool,
            _errcheck,
            [("Com_Num", c_long), ("Mono_Enum", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_Mono_Serial": (
            c_bool,
            _errcheck,
            [
                ("Serial_Num", c_long),
                ("Mono_Enum", POINTER(c_long)),
                ("Model", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Close_Enum": (c_bool, _errcheck, [("Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Valid_Mono_Enum": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Valid_v6_Mono_Enum": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_preOpen_Valid": (c_bool, _errcheck, [("Enum_Num", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_preOpen_Model_CharStr": (
            c_bool,
            _errcheck,
            [("Enum_Num", c_long), ("ModelStr", c_char_p), ("ModelStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_preOpen_Model_int32": (
            c_bool,
            _errcheck,
            [("Enum_Num", c_long), ("Model_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Send_CMD_To_Inst_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Enum", c_long),
                ("SendCMD", c_char_p),
                ("SendCMD_sz", c_long),
                ("RCV_Str", c_char_p),
                ("RCV_Str_sz", c_long),
                ("ms_TimeOut", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Model_CharStr": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("ModelStr", c_char_p), ("ModelStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Serial_CharStr": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("SerialStr", c_char_p), ("SerialStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Focallength": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Focallength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_HalfAngle": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("HalfAngle", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_DetectorAngle": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("DetectorAngle", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Double": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Double_Present", POINTER(c_bool)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Double_Subtractive": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Double_Subtractive", POINTER(c_bool)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Precision": (c_long, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Backlash_Steps": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Backlash", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Gear_Steps": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("minor_steps", POINTER(c_long)),
                ("major_steps", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_nmRev_Ratio": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("nmRev_Ratio", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_nmRev": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("nm", POINTER(c_double)),
                ("Rev", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_COM": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_preOpen_COM": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_PI_Calibrated": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grat_num", c_long),
                ("Calibrated", POINTER(c_bool)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_PI_Offset": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grat_num", c_long),
                ("PI_Offset", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_PI_GAdjust": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grat_num", c_long),
                ("PI_GAdjust", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_PI_FocalLength": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grat_num", c_long),
                ("PI_FocalLength", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_PI_HalfAngle": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grat_num", c_long),
                ("PI_HalfAngle", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_PI_DetAngle": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grat_num", c_long),
                ("PI_DetAngle", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_PI_Calibrated": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grat_num", c_long), ("Calibrated", c_bool), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_PI_Offset": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grat_num", c_long), ("PI_Offset", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_PI_GAdjust": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grat_num", c_long), ("PI_GAdjust", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_PI_FocalLength": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grat_num", c_long),
                ("PI_FocalLength", c_double),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_PI_HalfAngle": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grat_num", c_long), ("PI_HalfAngle", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_PI_DetAngle": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grat_num", c_long), ("PI_DetAngle", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Pixel_Map_nm": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Pixel_Size_um", c_double),
                ("Number_X_Pixels", c_long),
                ("Left_Adj_Percent", c_double),
                ("Center_Adj_Pixels", c_double),
                ("Right_Adj_Percent", c_double),
                ("Pixel_Map", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Pixel_Map_ang": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Pixel_Size_um", c_double),
                ("Number_X_Pixels", c_long),
                ("Left_Adj_Percent", c_double),
                ("Center_Adj_Pixels", c_double),
                ("Right_Adj_Percent", c_double),
                ("Pixel_Map", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Pixel_Map_eV": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Pixel_Size_um", c_double),
                ("Number_X_Pixels", c_long),
                ("Left_Adj_Percent", c_double),
                ("Center_Adj_Pixels", c_double),
                ("Right_Adj_Percent", c_double),
                ("Pixel_Map", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Pixel_Map_micron": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Pixel_Size_um", c_double),
                ("Number_X_Pixels", c_long),
                ("Left_Adj_Percent", c_double),
                ("Center_Adj_Pixels", c_double),
                ("Right_Adj_Percent", c_double),
                ("Pixel_Map", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Pixel_Map_absCM": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Pixel_Size_um", c_double),
                ("Number_X_Pixels", c_long),
                ("Left_Adj_Percent", c_double),
                ("Center_Adj_Pixels", c_double),
                ("Right_Adj_Percent", c_double),
                ("Pixel_Map", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Pixel_Map_relCM": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Pixel_Size_um", c_double),
                ("Number_X_Pixels", c_long),
                ("Laser_Line_nm", c_double),
                ("Left_Adj_Percent", c_double),
                ("Center_Adj_Pixels", c_double),
                ("Right_Adj_Percent", c_double),
                ("Pixel_Map", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Wavelength_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_nm_Stored": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Wavelength_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_ang": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Wavelength_ang": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_eV": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Wavelength_eV": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_micron": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Wavelength_micron": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_absCM": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Wavelength_absCM": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_relCM": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Center_nm", c_double),
                ("Wavelength", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Mono_Wavelength_relCM": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Center_nm", c_double), ("Wavelength", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_Cutoff_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_Min_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Wavelength_nm_ProcessTime": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("wavelength", c_double),
                ("processTime", POINTER(c_long)),
                ("errorCode", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Turret": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Turret", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Turret": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Turret", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Turret_Gratings": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Gratings_Per_Turret", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Turret_Max": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Max_Turret_Number", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Grating": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Grating": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Grating_ProcessTime": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating", c_long),
                ("processTime", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Grating_Blaze_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating", c_long),
                ("BlazeStr", c_char_p),
                ("BlazeStr_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Grating_Density": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating", c_long),
                ("Groove_MM", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Grating_Installed": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Grating_Max": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Max_Grating_Number", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Diverter_Valid": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Diverter_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Diverter_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Diverter_Num", c_long),
                ("Diverter_Pos", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Mono_Diverter_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Diverter_Num", c_long),
                ("Diverter_Pos", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Diverter_Pos_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Diverter_Num", c_long),
                ("Diverter_Pos", c_char_p),
                ("Diverter_Pos_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Slit_Type": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Slit_Pos", c_long),
                ("Slit_Type", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Slit_Type_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Slit_Pos", c_long),
                ("Slit_Type", c_char_p),
                ("Slit_Type_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Slit_Width": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Slit_Pos", c_long),
                ("Slit_Width", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Mono_Slit_Width": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Slit_Pos", c_long), ("Slit_Width", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Slit_Width_ProcessTime": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Slit_Pos", c_long),
                ("Slit_Width", c_long),
                ("processTime", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Slit_Max": (
            c_bool,
            _errcheck,
            [("monoEnum", c_long), ("slitPos", c_long), ("slitWith", POINTER(c_long)), ("errorCode", POINTER(c_long))],
        ),
        "ARC_Mono_Slit_Home": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Slit_Pos", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Slit_Name_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Slit_Num", c_long),
                ("Slit_NameStr", c_char_p),
                ("Slit_NameStr_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Calc_Mono_Slit_BandPass": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Slit_Pos", c_long),
                ("SlitWidth", c_double),
                ("BandPass", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Slit_BandPass": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Slit_Pos", c_long),
                ("BandPass", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Mono_Slit_BandPass": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Slit_Pos", c_long), ("BandPass", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Double_Intermediate_Slit": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Slit_Pos", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Exit_Slit": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Slit_Pos", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Filter_Present": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Filter_Position": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Position", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Filter_Position": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Position", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Filter_Position_ProcessTime": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Position", c_long),
                ("processTime", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Filter_Min_Pos": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Position", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Filter_Max_Pos": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Position", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Filter_Home": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_XYSample_Present": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_XYSample_XPosition_Inches": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("XPosition", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_XYSample_YPosition_Inches": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("YPosition", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_XYSample_XPosition_Inches": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("XPosition", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_XYSample_YPosition_Inches": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("YPosition", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_XYSample_HomeX": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Mono_XYSample_HomeY": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Sample_Present": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wheel_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Sample_Position": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Wheel_Num", c_long),
                ("Position", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Mono_Sample_Position": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wheel_Num", c_long), ("Position", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Sample_Home": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wheel_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Sample_WheelType_Index": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Wheel_Num", c_long),
                ("WheelType", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Sample_WheelType_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Wheel_Num", c_long),
                ("WheelType", c_char_p),
                ("WheelType_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Mono_Sample_WheelType": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wheel_Num", c_long), ("WheelType", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Sample_Min_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Wheel_Num", c_long),
                ("Position", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Sample_Max_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Wheel_Num", c_long),
                ("Position", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Mono_Int_Led_On": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_Mono_Int_Led": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Led_State", c_bool), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Motor_Int": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Wheel_Int": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Mono_Move_Steps": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Num_Steps", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Sine_Drive": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Init_Grating": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Init_Grating", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Init_Grating": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Init_Grating", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Init_Wave_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Init_Wave", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Init_Wave_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Init_Wave", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Init_ScanRate_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Init_ScanRate", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Init_ScanRate_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Init_ScanRate", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Grating_Offset": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Offset", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Grating_Gadjust": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Gadjust", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Grating_Offset": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Offset", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Grating_Gadjust": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Gadjust", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Grating_Calc_Offset": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating", c_long),
                ("Wave", c_double),
                ("RefWave", c_double),
                ("newOffset", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Grating_Calc_Gadjust": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating", c_long),
                ("Wave", c_double),
                ("RefWave", c_double),
                ("newGadjust", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Grating_UnInstall": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Reboot", c_bool), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Grating_Install_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating", c_long),
                ("Density", c_long),
                ("Blaze", c_char_p),
                ("Blaze_sz", c_long),
                ("NMBlaze", c_bool),
                ("umBlaze", c_bool),
                ("HOLBlaze", c_bool),
                ("MIRROR", c_bool),
                ("Reboot", c_bool),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Reset": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Mono_Restore_Factory_Settings": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Save_Factory_Settings": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("password", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_Scan_Rate_nm_min": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Scan_Rate", POINTER(c_double)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Mono_Scan_Rate_nm_min": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Scan_Rate", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Start_Scan_To_nm": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Wavelength_nm", c_double), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Scan_Done": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Done_Moving", POINTER(c_bool)),
                ("Current_Wavelength_nm", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Start_Jog": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Jog_MaxRate", c_bool), ("JogUp", c_bool), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Stop_Jog": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Shutter_Valid": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Shutter_Open": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_Mono_Shutter_Open": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_Mono_Shutter_Closed": (c_bool, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Open_ReadOut_SpectraHub": (
            c_bool,
            _errcheck,
            [("Port_Num", c_long), ("NCL_Enum", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_ReadOut_Port_SpectraHub": (
            c_bool,
            _errcheck,
            [("Com_Num", c_long), ("NCL_Enum", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_ReadOut": (
            c_bool,
            _errcheck,
            [
                ("Port_Num", c_long),
                ("NCL_Enum", POINTER(c_long)),
                ("Mono1_Enum", POINTER(c_long)),
                ("Mono2_Enum", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Open_ReadOut_Port": (
            c_bool,
            _errcheck,
            [
                ("Com_Num", c_long),
                ("NCL_Enum", POINTER(c_long)),
                ("Mono1_Enum", POINTER(c_long)),
                ("Mono2_Enum", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Valid_Enum": (c_bool, _errcheck, [("Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Valid_ReadOut_Enum": (c_bool, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_ReadOut_preOpen_Valid": (c_bool, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_ReadOut_preOpen_Model_int32": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Model_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_ReadOut_preOpen_Model_CharStr": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("ModelStr", c_char_p), ("ModelStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_ReadOut_Model_CharStr": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("ModelStr", c_char_p), ("ModelStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_ReadOut_Serial_CharStr": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("SerialStr", c_char_p), ("SerialStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_ReadOut_COM": (
            c_bool,
            _errcheck,
            [("Inst_Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_ReadOut_preOpen_COM": (
            c_bool,
            _errcheck,
            [("Inst_Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Add_Readout": (
            c_bool,
            _errcheck,
            [("Enum", c_long), ("Hub_Enum", c_long), ("SpectraHub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Readout_Device_Enum": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Device_Enum", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Num_Det": (c_long, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Valid_Det_Num": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_ReadOut_ITime_ms": (c_long, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_ReadOut_ITime_ms": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("ITime_ms", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_Type": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("DetType", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_Type_CharStr": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det_Num", c_long),
                ("DetType", c_char_p),
                ("DetType_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Det_Type": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("DetType", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Det_Photon": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Det_Voltage": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Det_Current": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_BiPolar": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_BiPolar_CharStr": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det_Num", c_long),
                ("BiPolarStr", c_char_p),
                ("BiPolarStr_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Det_BiPolar": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Det_UniPolar": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_Range": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Range", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_Range_Factor": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det_Num", c_long),
                ("Range_Factor", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_Det_Range": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Range", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_HV_on": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Det_HV_on": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Det_HV_off": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_HV_Volts": (
            c_long,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Det_HV_Volts": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("HV_Volts", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Det_NumAvgRead": (c_long, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_Det_NumAvgRead": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("NumReadsAvg", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_Det_Units": (c_long, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_NCL_Det_Units_Index": (c_long, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_NCL_Det_Units_String": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det_Num", c_long),
                ("ReadUnits_Str", c_char_p),
                ("ReadUnits_Str_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_set_NCL_Det_Units": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("ReadingUnits", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_NCL_Det_Units_Index": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("ReadingUnits", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_Det_Saturation": (
            c_double,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Det_Read": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det_Num", c_long),
                ("Read_Value", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Det_ReadAll": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det1_Value", POINTER(c_double)),
                ("Det2_Value", POINTER(c_double)),
                ("Det3_Value", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_start_TimeScan_SingleChannel": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det_Num", c_long),
                ("Interval", c_long),
                ("NumberPoints", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_stream_TimeScan_SingleChannel": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_start_TimeScan_AllChannels": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Interval", c_long), ("NumberPoints", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_stream_TimeScan_AllChannels": (c_bool, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_TimeScan_CurPointNum": (
            c_long,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_TimeScan_PointValue": (
            c_double,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Point_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_stop_TimeScan": (c_bool, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Det_Start_NonBlock_Read": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Det_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Det_NonBlock_Read_Done": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Det_Num", c_long),
                ("Read_Value", POINTER(c_double)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_NCL_Filter_Present": (c_bool, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_NCL_Filter_Present": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Min_Filter", c_long), ("Max_Filter", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_Filter_Position": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Position", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_NCL_Filter_Position": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Position", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_Filter_Position_ProcessTime": (
            c_bool,
            _errcheck,
            [
                ("NCL_Enum", c_long),
                ("Position", c_long),
                ("processTime", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_NCL_Filter_Min_Pos": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Min_Pos", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_Filter_Max_Pos": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Max_Pos", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_NCL_Filter_Home": (c_bool, _errcheck, [("NCL_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_NCL_Shutter_Valid": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Shutter_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_Shutter_Open": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Shutter_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_NCL_Shutter_Open": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Shutter_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_NCL_Shutter_Closed": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Shutter_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_SpectraHub_Shutter_Enabled": (
            c_bool,
            _errcheck,
            [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_SpectraHub_Shutter_Enable": (
            c_bool,
            _errcheck,
            [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_SpectraHub_Shutter_Disable": (
            c_bool,
            _errcheck,
            [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_SpectraHub_Shutter_Open_High": (
            c_bool,
            _errcheck,
            [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_SpectraHub_Shutter_Open_High": (
            c_bool,
            _errcheck,
            [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_SpectraHub_Shutter_Open_Low": (
            c_bool,
            _errcheck,
            [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_SpectraHub_Shutter_Open": (c_bool, _errcheck, [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_SpectraHub_Shutter_Open": (c_bool, _errcheck, [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_SpectraHub_Shutter_Closed": (
            c_bool,
            _errcheck,
            [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_TTL_Valid": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("TTL_Line", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_TTL_In": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("TTL_Line", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_TTL_Out": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("TTL_Line", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_NCL_TTL_Out_On": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("TTL_Line", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_NCL_TTL_Out_Off": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("TTL_Line", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_SpectraHub_Trig_On": (c_bool, _errcheck, [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_SpectraHub_Trig_On": (c_bool, _errcheck, [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_set_SpectraHub_Trig_Off": (c_bool, _errcheck, [("Hub_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_NCL_Mono_Setup": (
            c_bool,
            _errcheck,
            [("NCL_Enum", c_long), ("Mono_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_NCL_Mono_Enum": (
            c_long,
            _errcheck,
            [("NCL_Enum", c_long), ("Mono_Num", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_Filter": (
            c_bool,
            _errcheck,
            [("Enum_Num", c_long), ("Filter_Enum", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_Filter_Port": (
            c_bool,
            _errcheck,
            [("Com_Num", c_long), ("Filter_Enum", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Open_Filter_Serial": (
            c_bool,
            _errcheck,
            [
                ("Serial_Num", c_long),
                ("Filter_Enum", POINTER(c_long)),
                ("Model", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Valid_Filter_Enum": (c_bool, _errcheck, [("Filter_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Filter_preOpen_Valid": (c_bool, _errcheck, [("Enum_Num", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Filter_preOpen_Model_int32": (
            c_bool,
            _errcheck,
            [("Enum_Num", c_long), ("Model_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_preOpen_Model_CharStr": (
            c_bool,
            _errcheck,
            [("Enum_Num", c_long), ("ModelStr", c_char_p), ("ModelStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_Model_CharStr": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("ModelStr", c_char_p), ("ModelStr_sz", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_Serial_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Filter_Enum", c_long),
                ("SerialStr", c_char_p),
                ("SerialStr_sz", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Filter_COM": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_preOpen_COM": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("COMx", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_Present": (c_bool, _errcheck, [("Filter_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Filter_Position": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("Position", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_set_Filter_Position": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("Position", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_Position_ProcessTime": (
            c_bool,
            _errcheck,
            [
                ("Filter_Enum", c_long),
                ("Position", c_long),
                ("processTime", POINTER(c_long)),
                ("errorCode", POINTER(c_long)),
            ],
        ),
        "ARC_get_Filter_Min_Pos": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("Position", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_Max_Pos": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("Position", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Filter_Home": (c_bool, _errcheck, [("Filter_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_Mono_set_Model_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Model_Str", c_char_p),
                ("Model_Str_sz", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_set_Serial_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Serial_Str", c_char_p),
                ("Serial_Str_sz", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_get_Board_Serial_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Serial_Str", c_char_p),
                ("Serial_Str_sz", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_set_Board_Serial_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Serial_Str", c_char_p),
                ("Serial_Str_sz", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_set_Drive_Linear": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_set_nmRev": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("nm", c_double),
                ("Rev", c_double),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_set_Drive_Sine": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_set_Gratings_Per_Turret": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating_per_Turret", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_set_Halfangle": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("HalfAngle", c_double), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_set_Gear_Ratio": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("minor", c_long),
                ("major", c_long),
                ("base", c_double),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_set_Backlash": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Backlash", c_long), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Read_Motors": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("OnBoard1", POINTER(c_long)),
                ("OnBoard2", POINTER(c_long)),
                ("OnBoard3", POINTER(c_long)),
                ("Daughter1", POINTER(c_long)),
                ("Daughter2", POINTER(c_long)),
                ("Daughter3", POINTER(c_long)),
                ("Daughter4", POINTER(c_long)),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Use": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_Use", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Stop": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_Stop", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Speed": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_Speed", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_StepRev": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Steps_per_Rev", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_eeoptions": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Options_Str", c_char_p),
                ("Option_Str_sz", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Grating_Install_NoHello_CharStr": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Grating", c_long),
                ("Density", c_long),
                ("Blaze", c_char_p),
                ("Blaze_sz", c_long),
                ("NMBlaze", c_bool),
                ("umBlaze", c_bool),
                ("HOLBlaze", c_bool),
                ("MIRROR", c_bool),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Motor_Pos_Step": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_Pos", c_long),
                ("Step", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Motor_Min_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Min_Motor_Pos", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Motor_Max_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Max_Motor_Pos", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Grating_UnInstall_NoHello": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Grating", c_long), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_set_Focallength": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("FocalLength", c_long), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_set_DetectorAngle": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("DetAngle", c_double), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Clear_Mono_Setup": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Passwd", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Motor_set_SlitClamp": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Clamp_Value", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Read_Motors_SlitClamp": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("OnBoard1", POINTER(c_long)),
                ("OnBoard2", POINTER(c_long)),
                ("OnBoard3", POINTER(c_long)),
                ("Daughter1", POINTER(c_long)),
                ("Daughter2", POINTER(c_long)),
                ("Daughter3", POINTER(c_long)),
                ("Daughter4", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Read_Motors_SFreq": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("OnBoard1", POINTER(c_long)),
                ("OnBoard2", POINTER(c_long)),
                ("OnBoard3", POINTER(c_long)),
                ("Daughter1", POINTER(c_long)),
                ("Daughter2", POINTER(c_long)),
                ("Daughter3", POINTER(c_long)),
                ("Daughter4", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Read_Motors_Microns_to_Steps": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("OnBoard1", POINTER(c_long)),
                ("OnBoard2", POINTER(c_long)),
                ("OnBoard3", POINTER(c_long)),
                ("Daughter1", POINTER(c_long)),
                ("Daughter2", POINTER(c_long)),
                ("Daughter3", POINTER(c_long)),
                ("Daughter4", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Read_Motors_Steps_to_Microns": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("OnBoard1", POINTER(c_long)),
                ("OnBoard2", POINTER(c_long)),
                ("OnBoard3", POINTER(c_long)),
                ("Daughter1", POINTER(c_long)),
                ("Daughter2", POINTER(c_long)),
                ("Daughter3", POINTER(c_long)),
                ("Daughter4", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Read_Motors_SlitHome": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("OnBoard1", POINTER(c_long)),
                ("OnBoard2", POINTER(c_long)),
                ("OnBoard3", POINTER(c_long)),
                ("Daughter1", POINTER(c_long)),
                ("Daughter2", POINTER(c_long)),
                ("Daughter3", POINTER(c_long)),
                ("Daughter4", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_SFreq": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("SFreq_Value", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Microns_to_Steps": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Microns_to_Steps", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Steps_to_Microns": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Steps_to_Microns", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_SlitHome": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("SlitHome", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Slit_Hz": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Hz", POINTER(c_long)),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_Chan": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_Chan", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_StepStop": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Motor", c_long), ("StepStop", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Motor_get_Motor_Accel": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Motor", c_long), ("Accel", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Motor_get_Motor_lraf": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_lraf", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_hraf": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_hraf", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_mper": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_mper", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_set_Motor_mper": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Motor_mper", c_long),
                ("Passwd", c_long),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_App": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Motor", c_long), ("Motor_App", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Motor_get_Motor_Index_Min_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Index_Min_Pos", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_Index_Max_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Index_Max_Pos", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_Speed": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Motor", c_long), ("Speed", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Motor_get_Motor_Step_Offset": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Step_Offset", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_Mono_Motor_get_Motor_Step_Rev": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Motor", c_long), ("Step_Rev", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_Mono_Motor_get_Motor_Step_Pos": (
            c_bool,
            _errcheck,
            [
                ("Mono_Enum", c_long),
                ("Motor", c_long),
                ("Position", c_long),
                ("Step_Pos", POINTER(c_long)),
                ("Error_Code", POINTER(c_long)),
            ],
        ),
        "ARC_get_Filter_preOpen_Serial_int32": (
            c_bool,
            _errcheck,
            [("Filter_Enum", c_long), ("Serial_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Mono_preOpen_Serial_int32": (
            c_bool,
            _errcheck,
            [("Mono_Enum", c_long), ("Serial_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_ReadOut_preOpen_Serial_int32": (
            c_bool,
            _errcheck,
            [("ReadOut_Enum", c_long), ("Serial_int32", POINTER(c_long)), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_get_Filter_Serial_int32": (c_long, _errcheck, [("Filter_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_Mono_Serial_int32": (c_long, _errcheck, [("Mono_Enum", c_long), ("Error_Code", POINTER(c_long))]),
        "ARC_get_ReadOut_Serial_int32": (
            c_long,
            _errcheck,
            [("Readout_Enum", c_long), ("Error_Code", POINTER(c_long))],
        ),
        "ARC_SubscribeForPnPNotification": (c_long, _log_errcheck, [("cbf", c_void_p)]),
        "ARC_UnSubscribeForPnPNotification": (c_long, _log_errcheck, [("cbf", c_void_p)]),
    }

    # The following functions have not been implemented.
    # The function may be reserved to be used internally by Acton Research Corporation,
    # or, the function was not in the SDK manual.
    #
    # ARC_get_Enum_preOpen_Model_int32
    # ARC_get_Enum_Model
    # ARC_get_Enum_Model_int32
    # ARC_get_Enum_Serial
    # ARC_get_Enum_Serial_int32
    # ARC_get_Enum_COM
    # ARC_Open_ReadOut_SpectraHub
    # ARC_Open_ReadOut_Port_SpectraHub
    # ARC_Valid_v6_Mono_Enum
    # ARC_Mono_XYSample_HomeX
    # ARC_Mono_XYSample_HomeY
    # ARC_Mono_Sample_Home
    # ARC_Mono_Save_Factory_Settings
    # ARC_Mono_Read_Motors_SlitClamp
    # ARC_Mono_Read_Motors_SFreq
    # ARC_Mono_Read_Motors_Microns_to_Steps
    # ARC_Mono_Read_Motors_Steps_to_Microns
    # ARC_Mono_Read_Motors_SlitHome
    # ARC_Mono_Motor_get_Motor_Chan
    # ARC_Mono_Motor_get_Motor_StepStop
    # ARC_Mono_Motor_get_Motor_Accel
    # ARC_Mono_Motor_get_Motor_lraf
    # ARC_Mono_Motor_get_Motor_hraf
    # ARC_Mono_Motor_get_Motor_mper
    # ARC_Mono_Motor_get_Motor_App
    # ARC_Mono_Motor_get_Motor_Index_Min_Pos
    # ARC_Mono_Motor_get_Motor_Index_Max_Pos
    # ARC_Mono_Motor_get_Motor_Speed
    # ARC_Mono_Motor_get_Motor_Step_Offset
    # ARC_Mono_Motor_get_Motor_Step_Rev
    # ARC_Mono_Motor_get_Motor_Step_Pos
    # ARC_get_Mono_preOpen_Valid
    # ARC_get_Mono_preOpen_COM
    # ARC_get_Mono_COM
    # ARC_get_Mono_Wavelength_nm_Stored
    # ARC_get_Mono_Wavelength_nm_ProcessTime
    # ARC_get_Mono_Grating_ProcessTime
    # ARC_get_Mono_Slit_Width_ProcessTime
    # ARC_get_Mono_Filter_Position_ProcessTime
    # ARC_get_Mono_XYSample_Present
    # ARC_get_Mono_XYSample_XPosition_Inches
    # ARC_get_Mono_XYSample_YPosition_Inches
    # ARC_get_Mono_Sample_Present
    # ARC_get_Mono_Sample_Position
    # ARC_get_Mono_Sample_WheelType_Index
    # ARC_get_Mono_Sample_WheelType_CharStr
    # ARC_get_Mono_Sample_Min_Pos
    # ARC_get_Mono_Sample_Max_Pos
    # ARC_set_Mono_XYSample_XPosition_Inches
    # ARC_set_Mono_XYSample_YPosition_Inches
    # ARC_set_Mono_Sample_Position
    # ARC_set_Mono_Sample_WheelType
    # ARC_Send_CMD_To_Inst_CharStr
    # ARC_get_ReadOut_preOpen_Valid
    # ARC_get_ReadOut_preOpen_COM
    # ARC_get_ReadOut_COM
    # ARC_get_Readout_Device_Enum
    # ARC_Add_Readout
    # ARC_get_NCL_Det_Units
    # ARC_get_NCL_Det_Units_Index
    # ARC_get_NCL_Det_Units_String
    # ARC_get_NCL_Det_Saturation
    # ARC_get_NCL_Filter_Position_ProcessTime
    # ARC_set_NCL_Det_Units
    # ARC_set_NCL_Det_Units_Index
    # ARC_start_TimeScan_SingleChannel
    # ARC_start_TimeScan_AllChannels
    # ARC_stream_TimeScan_SingleChannel
    # ARC_stream_TimeScan_AllChannels
    # ARC_get_TimeScan_CurPointNum
    # ARC_get_TimeScan_PointValue
    # ARC_stop_TimeScan
    # ARC_get_Filter_preOpen_Valid
    # ARC_get_Filter_COM
    # ARC_get_Filter_preOpen_COM
    # ARC_get_Filter_Position_ProcessTime
    # ARC_SubscribeForPnPNotification
    # ARC_UnSubscribeForPnPNotification
    #
    # The following functions are in the SDK manual
    #
    # ARC_get_Mono_preOpen_Model_int32
    # ARC_get_Mono_preOpen_Serial_int32
    # ARC_get_Mono_Serial_int32
    # ARC_get_Filter_preOpen_Model_int32
    # ARC_get_Filter_preOpen_Serial_int32
    # ARC_get_Filter_Serial_int32
    # ARC_get_ReadOut_preOpen_Model_int32
    # ARC_get_ReadOut_preOpen_Serial_int32
    # ARC_get_ReadOut_Serial_int32
    # ARC_get_Mono_Pixel_Map_nm
    # ARC_get_Mono_Pixel_Map_ang
    # ARC_get_Mono_Pixel_Map_eV
    # ARC_get_Mono_Pixel_Map_micron
    # ARC_get_Mono_Pixel_Map_absCM
    # ARC_get_Mono_Pixel_Map_relCM
    # ARC_get_Mono_Slit_BandPass
    # ARC_set_Mono_Slit_BandPass
    # ARC_get_PI_Calibrated
    # ARC_get_PI_Offset
    # ARC_get_PI_GAdjust
    # ARC_get_PI_FocalLength
    # ARC_get_PI_HalfAngle
    # ARC_get_PI_DetAngle
    # ARC_set_PI_Calibrated
    # ARC_set_PI_Offset
    # ARC_set_PI_GAdjust
    # ARC_set_PI_FocalLength
    # ARC_set_PI_HalfAngle
    # ARC_set_PI_DetAngle
    # ARC_get_SpectraHub_Shutter_Enabled
    # ARC_set_SpectraHub_Shutter_Enable
    # ARC_set_SpectraHub_Shutter_Disable
    # ARC_get_SpectraHub_Shutter_Open_High
    # ARC_set_SpectraHub_Shutter_Open_High
    # ARC_set_SpectraHub_Shutter_Open_Low
    # ARC_get_SpectraHub_Shutter_Open
    # ARC_set_SpectraHub_Shutter_Open
    # ARC_set_SpectraHub_Shutter_Closed
    # ARC_get_SpectraHub_Trig_On
    # ARC_set_SpectraHub_Trig_On
    # ARC_set_SpectraHub_Trig_Off

    sdk = LoadLibrary(path, "windll").lib

    # Make sure that the version of the DLL is okay.
    # Used the header file from ARC_Instrument v2.0.3 to implement this wrapper.
    # The wrapper seems to be compatible with v5.0.0.
    # The wrapper is not compatible with v0.1.4 nor v0.2.9.
    sdk.ARC_Ver.argtypes = [typ for _, typ in functions["ARC_Ver"][2]]
    major, minor, build = PrincetonInstruments.ver()
    if major < 2:  # noqa: PLR2004
        msg = (
            f"PrincetonInstrumentsError: The minimum compatible DLL version is 2.0.0\n"
            f"You are using version {major}.{minor}.{build}"
        )
        raise RuntimeError(msg)

    for key, value in functions.items():  # pyright: ignore[reportUnknownVariableType]
        attr = getattr(sdk, key)
        attr.restype, attr.errcheck = value[:2]
        attr.argtypes = [typ for _, typ in value[2]]

    if not sdk.ARC_Init():
        msg = "PrincetonInstrumentsError: Cannot initialize the SDK"
        raise RuntimeError(msg)

    PrincetonInstruments._SDK = sdk  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

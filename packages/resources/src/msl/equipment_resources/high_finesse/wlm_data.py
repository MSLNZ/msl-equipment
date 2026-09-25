"""Wrapper around the wlmData library from HighFinesse."""

from __future__ import annotations

import sys
from ctypes import c_bool, c_char_p, c_double, c_long, c_ulong, c_ushort, c_void_p, create_string_buffer
from typing import TYPE_CHECKING

from msl.loadlib import Client64, Server32

if TYPE_CHECKING:
    from ctypes import _CFunctionType  # pyright: ignore[reportPrivateUsage]
    from typing import Any


ERROR_CODES = {
    -1: "The device has not detected a signal",
    -2: "The device has not detected a calculable signal",
    -3: "The signal is too small to be calculated properly",
    -4: "The signal is too large to be calculated properly",
    -5: "The device is not active",
    -6: "This function is not available for this device version",
    -7: "Nothing changed",
    -8: "The detected signal could not be divided in to separate pulses",
    -10: "Channel not available",
    -13: "Division by Zero",
    -14: "One of the device parameters is out of range",
    -15: "One of the unit parameters is out of range",
    -16: "WOCalc",
    -26: "TCP error",
    -28: "Parameter out of range",
    -29: "String too long",
    -30: "Interrupted by user",
    -31: "Info already fetched",
    -32: "No value yet",
    -33: "No new value yet",
    -1000: "The device has not (yet) measured the temperature",
    -1005: "The HighFinesse software is not running",
    -1006: "The device does not support a temperature measurement",
    -1000000005: "The HighFinesse software is not running",
    -1000000006: "Distance not available",
}

SET_ERROR_CODES = {
    -1: "The HighFinesse software is not running",
    -2: "Could not set value",
    -3: "Parameter out of range",
    -4: "Device out of resources",
    -5: "Internal error",
    -6: "Not available",
    -7: "Busy",
    -8: "Not in measurement mode",
    -9: "Only in measurement mode",
    -10: "Channel not available",
    -11: "Channel temporarily not available",
    -12: "Calibration option not available",
    -13: "Calibration wavelength out of range",
    -14: "Bad calibration signal",
    -15: "Unit not available",
    -16: "File not found",
    -17: "File creation",
    -18: "Trigger pending",
    -19: "Trigger waiting",
    -20: "No legitimation",
    -21: "No TCP legitimation",
    -22: "Not in pulse mode",
    -23: "Only in pulse mode",
    -24: "Not in switch mode",
    -25: "Only in switch mode",
    -26: "TCP error",
    -29: "String too long",
    -30: "Interrupted by user",
}

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from ctypes import WINFUNCTYPE

    func_type = WINFUNCTYPE
else:
    from ctypes import CFUNCTYPE

    func_type = CFUNCTYPE

Callback: type[_CFunctionType] = func_type(None, c_long, c_long, c_long, c_double, c_long)
"""[CFUNCTYPE][ctypes.CFUNCTYPE] function to use when a new measurement is available."""


def check(r: int) -> int:
    """Check the result for an error.

    The input type could also be a float but it's value is equivalent to an int,
    for example, -1005.0 is returned for the ErrTempWlmMissing error.

    Returns the result if there is no error.
    """
    if r < 0:
        msg = "HighFinesseError: " + ERROR_CODES.get(r, f"Undefined error code {r}")
        raise RuntimeError(msg)
    return r


def check_set(r: int) -> int:
    """Check the result of a "Set*" function for an error.

    Returns the result if there is no error.
    """
    if r < 0:
        msg = "HighFinesseError: " + SET_ERROR_CODES.get(r, f"Undefined error code {r}")
        raise RuntimeError(msg)
    return r


class WLMDataServer(Server32):
    """Wrapper around the wlmData library from HighFinesse."""

    def __init__(self, host: str, port: int, path: str) -> None:
        """Wrapper around the wlmData library from HighFinesse."""
        super().__init__(path, "windll" if sys.platform == "win32" else "cdll", host, port)

        signatures = [
            ("ControlWLM", c_long, (c_long, c_char_p, c_long)),
            ("GetWLMCount", c_long, (c_long,)),
            ("GetAnalysisMode", c_bool, (c_bool,)),
            ("SetAnalysisMode", c_long, (c_bool,)),
            ("GetExposureMode", c_bool, (c_bool,)),
            ("SetExposureMode", c_long, (c_bool,)),
            ("GetExposureNum", c_long, (c_long, c_long, c_long)),
            ("SetExposureNum", c_long, (c_long, c_long, c_long)),
            ("GetLinewidthMode", c_bool, (c_bool,)),
            ("SetLinewidthMode", c_long, (c_bool,)),
            ("GetPulseMode", c_ushort, (c_ushort,)),
            ("SetPulseMode", c_long, (c_ushort,)),
            ("GetRange", c_ushort, (c_ushort,)),
            ("SetRange", c_long, (c_ushort,)),
            ("GetWideMode", c_ushort, (c_ushort,)),
            ("SetWideMode", c_long, (c_ushort,)),
            ("SetPattern", c_long, (c_long, c_long)),
            ("GetPatternDataNum", c_long, (c_long, c_long, c_void_p)),
            ("GetPatternItemCount", c_long, (c_long,)),
            ("GetPatternItemSize", c_long, (c_long,)),
            ("GetWLMVersion", c_ulong, (c_long,)),
            ("GetTemperature", c_double, (c_double,)),
            ("GetWavelength", c_double, (c_double,)),
            ("GetWavelength2", c_double, (c_double,)),
            ("GetWavelengthNum", c_double, (c_long, c_double)),
            ("GetFrequency", c_double, (c_double,)),
            ("GetFrequency2", c_double, (c_double,)),
            ("GetFrequencyNum", c_double, (c_long, c_double)),
            ("GetLinewidth", c_double, (c_long, c_double)),
            ("Operation", c_long, (c_ushort,)),
            ("ConvertUnit", c_double, (c_double, c_long, c_long)),
            ("Instantiate", c_void_p, (c_long, c_long, c_void_p, c_long)),
        ]
        for name, res, args in signatures:
            try:
                fcn = getattr(self.lib, name)
            except AttributeError:
                # Some DLL's have different functions, for example,
                # GetLinewidthMode might not be in wlmData.dll if the
                # device does not support measuring the linewidth
                continue
            fcn.argtypes = args
            fcn.restype = res

    def get_analysis_mode(self) -> bool:
        """Get analysis mode state."""
        b: bool = self.lib.GetAnalysisMode(0)  # input argument is reserved for future use
        return b

    def get_exposure_mode(self) -> bool:
        """Get auto-exposure mode state."""
        b: bool = self.lib.GetExposureMode(0)  # input argument is reserved for future use
        return b

    def get_exposure_num(self, channel: int, index: int) -> int:
        """Returns the exposure time (in ms)."""
        r: int = self.lib.GetExposureNum(channel, index, 0)  # last argument is reserved for future use
        return r

    def control_wlm(self, action: int, path: bytes) -> int:
        """Start, hide or terminate the WLM server application."""
        r: int = self.lib.ControlWLM(action, create_string_buffer(path), 0)
        return r

    def convert_unit(self, value: float, frm: int, to: int) -> float:
        """Convert a value into a representation of another unit."""
        v: float = self.lib.ConvertUnit(value, frm, to)
        return v

    def get_temperature(self) -> float:
        """Returns the temperature inside the device, in Celsius."""
        t: float = self.lib.GetTemperature(0.0)  # input argument is reserved for future use
        return t

    def get_wavelength_num(self, number: int) -> float:
        """Returns the vacuum wavelength (in nm)."""
        w: float = self.lib.GetWavelengthNum(number, 0.0)  # second argument is reserved for future use
        return w

    def get_wlm_count(self) -> int:
        """Returns the number of wavelength meter and spectrum-analyser applications that are running."""
        count: int = self.lib.GetWLMCount(0)  # input argument is reserved for future use
        return count

    def get_wlm_version(self) -> list[int]:
        """Returns version information about the device."""
        return [check(self.lib.GetWLMVersion(i)) for i in range(4)]

    def instantiate(self, rfc: int, mode: int, p1: Any, p2: int) -> int:  # noqa: ANN401
        """Instantiate the device."""
        r: int = self.lib.Instantiate(rfc, mode, p1, p2)
        return r

    def interferometer_data(self, index: int, channel: int) -> list[int]:
        """Get the interferometer pattern data."""
        _ = check_set(self.lib.SetPattern(index, 1))  # cPatternEnable = 1
        c_size = c_ushort if self.lib.GetPatternItemSize(index) == 2 else c_ulong  # noqa: PLR2004
        count = self.lib.GetPatternItemCount(index)
        array = (c_size * count)()
        if self.lib.GetPatternDataNum(channel, index, array) == 0:
            msg = "Cannot get the interferometer pattern data"
            raise RuntimeError(msg)
        return list(array)

    def operation(self, mode: int) -> int:
        """Set the program measurement action mode and enables loading and recording files."""
        r: int = self.lib.Operation(mode)
        return r

    def set_analysis_mode(self, mode: bool) -> int:  # noqa: FBT001
        """Set the analysis mode state."""
        r: int = self.lib.SetAnalysisMode(mode)
        return r

    def set_exposure_mode(self, mode: bool) -> int:  # noqa: FBT001
        """Set the auto-exposure mode state."""
        r: int = self.lib.SetExposureMode(mode)
        return r

    def set_exposure_time(self, ms: int, channel: int, index: int) -> int:
        """Set the exposure time (in ms)."""
        t: int = self.lib.SetExposureNum(channel, index, ms)
        return t


class WLMData(Client64):
    """Wrapper around the wlmData library from HighFinesse."""

    def __init__(self, *, host: str | None, path: str) -> None:
        """Wrapper around the wlmData library from HighFinesse.

        The `path` can be to either a 32-bit or 64-bit version of the library.
        """
        super().__init__(__file__, host=host, path=path)

    def control_wlm(self, *, action: int, path: bytes) -> int:
        """Start, hide or terminate the WLM server application."""
        r: int = self.request32("control_wlm", action, path)
        return r

    def convert_unit(self, *, value: float, frm: int, to: int) -> float:
        """Convert a value into a representation of another unit."""
        return check(self.request32("convert_unit", value, frm, to))

    def get_analysis_mode(self) -> bool:
        """Get analysis mode state."""
        m: bool = self.request32("get_analysis_mode")
        return m

    def get_exposure_mode(self) -> bool:
        """Get auto-exposure mode state."""
        m: bool = self.request32("get_exposure_mode")
        return m

    def get_exposure_num(self, *, channel: int, index: int) -> int:
        """Returns the exposure time (in ms)."""
        return check(self.request32("get_exposure_num", channel, index))

    def get_temperature(self) -> float:
        """Returns the temperature inside the device, in Celsius."""
        t: float = check(self.request32("get_temperature"))
        return t

    def get_wavelength_num(self, number: int) -> float:
        """Returns the vacuum wavelength (in nm)."""
        w: float = check(self.request32("get_wavelength_num", number))
        return w

    def get_wlm_count(self) -> int:
        """Returns the number of wavelength meter and spectrum-analyser applications that are running."""
        count: int = self.request32("get_wlm_count")
        return count

    def get_wlm_version(self) -> list[int]:
        """Returns version information about the device."""
        version: list[int] = self.request32("get_wlm_version")
        return version

    def instantiate(self, *, rfc: int, mode: int, p1: Any, p2: int) -> int:  # noqa: ANN401
        """Instantiate the device."""
        r: int = self.request32("instantiate", rfc, mode, p1, p2)
        return r

    def interferometer_data(self, *, index: int, channel: int) -> list[int]:
        """Get the interferometer pattern data."""
        data: list[int] = self.request32("interferometer_data", index, channel)
        return data

    def operation(self, mode: int) -> int:
        """Set the program measurement action mode and enables loading and recording files."""
        return check_set(self.request32("operation", mode))

    def set_analysis_mode(self, mode: bool) -> None:  # noqa: FBT001
        """Set the analysis mode state."""
        _ = check_set(self.request32("set_analysis_mode", mode))

    def set_exposure_mode(self, mode: bool) -> None:  # noqa: FBT001
        """Set the auto-exposure mode state."""
        _ = check_set(self.request32("set_exposure_mode", mode))

    def set_exposure_time(self, *, ms: int, channel: int, index: int) -> None:
        """Set the exposure time (in ms)."""
        _ = check_set(self.request32("set_exposure_time", ms, channel, index))

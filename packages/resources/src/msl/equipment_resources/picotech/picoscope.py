"""A wrapper around the PicoScope SDK.

The main class is [PicoScope][msl.equipment_resources.picotech.picoscope.PicoScope].
The other classes are enumerations and structs from the SDK. Version 11.1.0.418 of
the SDK was used as a reference.

!!! warning
    This class was written for the ps5000a SDK. Different SDKs (e.g., ps4000a) have
    similar function signatures and may or may not work with this class. Note that Pico
    Technology have their own [repository](https://github.com/picotech){:target="_blank"}
    to support their products.
"""

# cSpell: ignore SINC PRBS FUNCTYPE nsegments
from __future__ import annotations

import math
import re
import sys
import time
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_char_p,
    c_double,
    c_float,
    c_int8,
    c_int16,
    c_int32,
    c_int64,
    c_uint16,
    c_uint32,
    c_uint64,
    c_void_p,
    create_string_buffer,
)
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, final

import numpy as np
from msl.loadlib import LoadLibrary
from numpy.ctypeslib import ndpointer

from msl.equipment.interfaces import SDK, MSLConnectionError
from msl.equipment.utils import to_enum

from .status import PICO_BUSY, PICO_OK, PICO_STATUS, Error, PicoInfo

if TYPE_CHECKING:
    from collections.abc import Sequence
    from ctypes import _CFunctionType  # pyright: ignore[reportPrivateUsage]
    from typing import Any, Callable, Never

    from msl.loadlib.types import PathLike
    from numpy.typing import NDArray

    from msl.equipment.schema import Equipment

    from ..types import (  # noqa: TID252
        PicoTechBlockReadyCallback,
        PicoTechDataReadyCallback,
        PicoTechStreamingReadyCallback,
    )


IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    from ctypes import WINFUNCTYPE as FUNCTYPE
else:
    from ctypes import CFUNCTYPE as FUNCTYPE


class PicoScope(SDK, manufacturer=r"Pico\s*Tech", model=r"[23456]\d{3}[A-Z]"):
    """A wrapper around the PicoScope API Series SDK."""

    streaming_done: bool = False
    """Whether streaming mode has finished acquiring the samples."""

    def __init__(self, equipment: Equipment) -> None:
        """A wrapper around the PicoScope API Series SDK.

        !!! warning
            This class was written for the ps5000a SDK. Different SDKs (e.g., ps4000a) have
            similar function signatures and may or may not work with this class. Note that Pico
            Technology have their own [repository](https://github.com/picotech){:target="_blank"}
            to support their products.

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for a PicoScope.

        Attributes: Connection Properties:
            auto_select_power (bool): PicoScopes that can be powered by either DC power or by USB power
                may raise an exception if the DC power supply is not connected. Setting `auto_select_power`
                to `True` will automatically switch to the USB power source. _Default: `True`_
            resolution (str): The device resolution (bit depth).
                Possible values are `8bit`, `12bit`, `14bit`, `15bit` or `16bit`. _Default: `12bit`_
        """
        self._handle: int = -1
        super().__init__(equipment, libtype="windll" if IS_WINDOWS else "cdll")
        self._prefix: str = Path(self.path).stem.lower()
        _configure(self._prefix, self.sdk, self._errcheck_api)

        assert equipment.connection is not None  # noqa: S101
        props = equipment.connection.properties
        dr = props.get("resolution", DeviceResolution.DR_12BIT)
        resolution = to_enum(dr, DeviceResolution, to_upper=True, prefix="DR_")

        handle = c_int16()
        serial = create_string_buffer(self.equipment.serial.encode())
        if self._prefix in {"ps5000a", "ps6000a"}:
            power_state = self._f("OpenUnit", byref(handle), serial, resolution)
        else:
            power_state = self._f("OpenUnit", byref(handle), serial)
        self._handle = handle.value

        # Check for PICO_POWER_SUPPLY_NOT_CONNECTED, PICO_USB3_0_DEVICE_NON_USB3_0_PORT
        if power_state in {0x11A, 0x11E}:
            if not props.get("auto_select_power", True):
                raise MSLConnectionError(self, Error[power_state])
            self._f("ChangePowerSource", self._handle, power_state)
        elif power_state != PICO_OK:
            raise MSLConnectionError(self, Error[power_state])

        self._channels: dict[str, ChannelSettings] = {}
        self._num_captures: int = 1
        self._pre_trigger: float = 0.0
        self._buffer_size: int = -1
        self._error_code: int = 0

        # the following are re-defined by calling set_timebase()
        self._sampling_interval: float = -1.0
        self._streaming_sampling_interval: int = -1
        self._num_samples: int = -1
        self._timebase_index: int = -1
        self._streaming_time_units: _TimeUnits = _TimeUnits.S

    def _f(self, name: str, *args: Any) -> Any:  # noqa: ANN401
        """Call the SDK function."""
        return getattr(self._sdk, self._prefix + name)(*args)

    def _errcheck_api(self, result: Any, func: Any, args: Any) -> Any:  # noqa: ANN401
        """The SDK function returns PICO_OK if the function call was successful."""
        self._log_errcheck(result, func, args)
        if result == PICO_OK:
            return result

        self._error_code = result
        msg = Error.get(result, f"UnknownPicoTechError: Error code 0x{result:08x}")
        raise MSLConnectionError(self, msg)

    def _get_timebase_index(self, dt: float, resolution: DeviceResolution | None = None) -> float:  # noqa: PLR0911
        """See the manual for the sample interval formula as a function of device resolution.

        Returns:
            The timebase index, `n` based on the table in the manual.
        """
        if resolution is None:
            resolution = self.get_device_resolution()

        if resolution == DeviceResolution.DR_8BIT:
            if dt < 8e-9:  # noqa: PLR2004
                return math.log2(1e9 * dt)
            return 125e6 * dt + 2

        if resolution == DeviceResolution.DR_12BIT:
            if dt < 16e-9:  # noqa: PLR2004
                return math.log2(500e6 * dt) + 1
            return 62.5e6 * dt + 3

        if resolution == DeviceResolution.DR_16BIT:
            if dt < 32e-9:  # noqa: PLR2004
                return 4
            return 62.5e6 * dt + 3

        # 14- and 15-bit resolution are the same
        if dt < 16e-9:  # noqa: PLR2004
            return 3
        return 125e6 * dt + 2

    @property
    def channel(self) -> dict[str, ChannelSettings]:
        """The configuration settings of each channel."""
        return self._channels

    @property
    def dt(self) -> float:
        """The time interval between samples (i.e., &Delta;t)."""
        return self._sampling_interval

    @property
    def pre_trigger(self) -> float:
        """The number of seconds that samples were acquired for before the trigger event."""
        return self._pre_trigger

    def channel_combinations_stateless(
        self, *, dt: float, resolution: DeviceResolution | str | int, ac_adaptor: bool = False
    ) -> ChannelFlags:
        """Get the channel and port combination flags for a proposed device configuration.

        It does not write the configuration to the device.

        Args:
            dt: The proposed sampling interval, in seconds.
            resolution: The resolution mode in which you propose to operate the oscilloscope.
                Can be an enum member name (case insensitive, with or without the "DR_" prefix) or value.
            ac_adaptor: Whether the proposed configuration uses the external AC adaptor or not.

        Returns:
            The channel and port combination flags.
        """
        n_combos = c_uint32()
        resolution = to_enum(resolution, DeviceResolution, prefix="DR_", to_upper=True)
        timebase = round(self._get_timebase_index(float(dt), resolution))
        ac = int(ac_adaptor)

        self._f("ChannelCombinationsStateless", self._handle, None, byref(n_combos), resolution, timebase, ac)

        c_flags = (c_uint32 * n_combos.value)()
        self._f("ChannelCombinationsStateless", self._handle, c_flags, byref(n_combos), resolution, timebase, ac)

        flags = [ChannelFlags(flag) for flag in sorted(c_flags)]
        if not flags:  # ideally, the SDK would return a non-zero PICO_STATUS value before this check
            msg = "No channel combinations for the proposed settings"
            raise MSLConnectionError(self, msg)

        combo = flags[0]
        for f in flags[1:]:
            combo |= f
        return combo

    def check_for_update(self) -> tuple[str, str, bool]:
        """Check if the firmware version requires an update.

        Returns:
            The current version, the latest version and whether an update is required,
                i.e., `(current, latest, is_required)`.
        """
        current = (c_uint16 * 4)()
        latest = (c_uint16 * 4)()
        required = c_uint16()
        self._f("CheckForUpdate", self._handle, byref(current), byref(latest), byref(required))
        current_str = ".".join(str(x) for x in current)
        latest_str = ".".join(str(x) for x in latest)
        return current_str, latest_str, bool(required.value)

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Disconnect from the PicoScope."""
        if self._handle >= 0:
            self._f("CloseUnit", self._handle)
            self._handle = -1
            super().disconnect()

    @staticmethod
    def enumerate_units(path: PathLike) -> list[str]:
        """Find PicoScopes that are connected to the computer.

        !!! note
            You cannot call this function after you have opened a connection to a PicoScope.

        Args:
            path: The path to the Pico Technology SDK of the scope models to find.
                You may specify the filename (e.g., `ps5000a`) if the parent directory
                is available on the PATH environment variable.

        Returns:
            A list of serial numbers of the PicoScopes that were found.
        """
        count = c_int16()
        serials = create_string_buffer(1024)
        size = c_int16(len(serials))
        sdk = LoadLibrary(path, libtype="windll" if IS_WINDOWS else "cdll")
        prefix = Path(sdk.path).stem.lower()
        result = getattr(sdk.lib, prefix + "EnumerateUnits")(byref(count), serials, byref(size))
        if result == PICO_OK:
            return serials.value.decode("utf-8").split(",")

        msg = Error.get(result, f"UnknownPicoTechError: Error code 0x{result:08x}")
        raise OSError(msg)

    def flash_led(self, start: int) -> None:
        """Flashes the LED on the front of the scope without blocking the calling thread.

        Args:
            start: The action required:

                * &lt; 0: flash the LED indefinitely
                * = 0: stop the LED flashing
                * &gt; 0: flash the LED `start` times. If the LED is already flashing, the
                    count will reset to `start`.

        """
        self._f("FlashLed", self._handle, start)

    def get_analogue_offset(
        self,
        range: Range | str | int,  # noqa: A002
        coupling: Coupling | str | int = "dc",
    ) -> tuple[float, float]:
        """Get the minimum and maximum allowable analogue offset for a specific voltage range.

        Args:
            range: The input voltage range. Can be an enum member name (with or without the `"R_"` prefix) or value.
            coupling: The impedance and coupling type. Can be an enum member name (case insensitive) or value.

        Returns:
            The `(minimum, maximum)` offset values.
        """
        _range = to_enum(range, Range, prefix="R_")
        _coupling = to_enum(coupling, Coupling, to_upper=True)
        maximum = c_float()
        minimum = c_float()
        self._f("GetAnalogueOffset", self._handle, _range, _coupling, byref(maximum), byref(minimum))
        return minimum.value, maximum.value

    def get_channel_information(
        self, channel: Channel | str | int, info: ChannelInfo | str | int = "ranges"
    ) -> list[int]:
        """Get information about a channel.

        Args:
            channel: The channel to get the ranges of. Can be an enum member name (case insensitive) or value.
            info: The information to get for the `channel`. Can be an enum member name (case insensitive) or value.

        Returns:
            The information that was requested.
        """
        ch = to_enum(channel, Channel, to_upper=True)
        info = to_enum(info, ChannelInfo, to_upper=True)
        c_array = (c_int32 * 50)()
        length = c_int32(len(c_array))
        self._f("GetChannelInformation", self._handle, info, 0, c_array, byref(length), ch)
        return [c_array[i] for i in range(length.value)]

    def get_device_resolution(self) -> DeviceResolution:
        """Get the device resolution.

        Returns:
            The resolution (bit depth).
        """
        resolution = c_uint32()
        self._f("GetDeviceResolution", self._handle, byref(resolution))
        return DeviceResolution(resolution.value)

    def get_max_down_sample_ratio(self, n: int, mode: RatioMode | str | int = "none", segment: int = 0) -> int:
        """Get the maximum down-sampling ratio.

        Args:
            n: The number of unprocessed samples to be downsampled.
            mode: The down-sampling mode. Can be an enum member name (case insensitive) or value.
            segment: The index of the memory segment to use.

        Returns:
            The maximum down-sampling ratio that can be used for a given number of samples
                in a given down-sampling mode.
        """
        mode = to_enum(mode, RatioMode, to_upper=True)
        ratio = c_uint32()
        self._f("GetMaxDownSampleRatio", self._handle, n, byref(ratio), mode, segment)
        return ratio.value

    def get_max_segments(self) -> int:
        """Get the maximum number of segments allowed for the opened device.

        Returns:
            This function returns the maximum number of segments allowed for the opened device.
                This number is the maximum value of `num_segments` that can be passed to
                [memory_segments][msl.equipment_resources.picotech.picoscope.PicoScope.memory_segments].
        """
        max_segments = c_uint32()
        self._f("GetMaxSegments", self._handle, byref(max_segments))
        return max_segments.value

    def get_minimum_timebase_stateless(self, *, flags: ChannelFlags, resolution: DeviceResolution | str | int) -> float:
        """Get the fastest available sample interval for the proposed configuration.

        It does not write the configuration to the device.

        Args:
            flags: The proposed combination of enabled channels and ports. To specify multiple
                channels and ports, use the bitwise-OR of the relevant
                [ChannelFlags][msl.equipment_resources.picotech.picoscope.ChannelFlags].
            resolution: The resolution mode in which you propose to operate the oscilloscope.
                Can be an enum member name (case insensitive, with or without the "DR_" prefix) or value.

        Returns:
            The fastest sampling interval, in seconds, corresponding to the proposed configuration.
        """
        timebase = c_uint32()
        dt = c_double()
        resolution = to_enum(resolution, DeviceResolution, prefix="DR_", to_upper=True)
        self._f("GetMinimumTimebaseStateless", self._handle, flags, byref(timebase), byref(dt), resolution)
        return dt.value

    def get_no_of_captures(self, *, pre_allocate: bool = True) -> int:
        """Get the number of captures available.

        Args:
            pre_allocate: Whether to pre-allocate a numpy array to hold the samples for each channel that is enabled.
                Allocation happens only once per run.

        Returns:
            The number of captures the device has made in rapid-block mode,
                since [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block] was called.
        """
        n_captures = c_uint32()
        self._f("GetNoOfCaptures", self._handle, byref(n_captures))
        n = n_captures.value
        if pre_allocate:
            if not self._channels:
                msg = "Must call set_channel() to configure all channels before get_no_of_captures()"
                raise MSLConnectionError(self, msg)

            if self._num_samples < 0:
                msg = "Must call set_timebase() before get_no_of_captures()"
                raise MSLConnectionError(self, msg)

            for channel in self._channels.values():
                if channel.enabled:
                    channel.allocate(num_samples=self._num_samples, num_captures=n)

        return n

    def get_num_of_processed_captures(self) -> int:
        """Get the number of captures in rapid block mode that have been processed.

        Returns:
            The number of available captures that have been collected after calling
                [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block].
        """
        n_processed_captures = c_uint32()
        self._f("GetNoOfProcessedCaptures", self._handle, byref(n_processed_captures))
        return n_processed_captures.value

    def get_streaming_latest_values(self, callback: PicoTechStreamingReadyCallback, *, strict: bool = False) -> None:
        """Instructs the driver to return the next block of values to your callback function.

        You must have previously called
        [run_streaming][msl.equipment_resources.picotech.picoscope.PicoScope.run_streaming]
        beforehand to set up streaming.

        Args:
            callback: The callback function to be called when the latest streaming samples
                have been acquired (see also,
                [wait_until_ready][msl.equipment_resources.picotech.picoscope.PicoScope.wait_until_ready] and
                [is_ready][msl.equipment_resources.picotech.picoscope.PicoScope.is_ready]).
            strict: Whether to raise an exception if the device is busy so data cannot be
                acquired yet when this method is called.
        """
        try:
            self._f("GetStreamingLatestValues", self._handle, callback, None)
        except MSLConnectionError:
            if self._error_code == PICO_BUSY and not strict:
                return
            raise

    def get_timebase2(self, timebase: int, num_samples: int = 0, segment: int = 0) -> tuple[float, int]:
        """Get the timebase.

        This function calculates the sampling interval and maximum number of samples for a given timebase under
        the specified conditions. The result will depend on the number of channels enabled.

        Args:
            timebase: The timebase.
            num_samples: The number of samples required.
            segment: The index of the memory segment to use.

        Returns:
            The sampling interval, in seconds, and the maximum number of samples available.
        """
        dt = c_float()
        max_samples = c_int32()
        self._f("GetTimebase2", self._handle, timebase, num_samples, byref(dt), byref(max_samples), segment)
        return dt.value * 1e-9, max_samples.value

    def get_trigger_info_bulk(self, from_segment: int = 0, to_segment: int | None = None) -> TriggerInfo:
        """Get information about the trigger point in one or more segments of captured data.

        If `from_segment` > `to_segment`, the segment index will wrap from the last segment back to 0.

        Args:
            from_segment: The zero-based number of the first segment of interest.
            to_segment: The zero-based number of the last segment of interest. If `None`,
                the last segment is determined from the number of captures.

        Returns:
            The trigger-information struct.
        """
        n = self.get_no_of_captures()
        if to_segment is None:
            to_segment = n - 1

        ti = _TriggerInfo()
        self._f("GetTriggerInfoBulk", self._handle, byref(ti), from_segment, to_segment)
        if ti.status != PICO_OK:
            msg = Error.get(ti.status, f"UnknownPicoTechError: Error code 0x{ti.status:08x}")
            raise MSLConnectionError(self, msg)

        return TriggerInfo(
            segment_index=ti.segmentIndex,
            trigger_time=ti.triggerTime * _TimeUnits.to_float(ti.timeUnits),
            trigger_index=ti.triggerIndex,
            timestamp_counter=ti.timeStampCounter,
        )

    def get_trigger_time_offset64(self, segment: int = 0) -> float:
        """Gets the time at which the trigger occurred.

        Call it after block-mode data has been captured or when data has been retrieved from a
        previous block-mode capture.

        Args:
            segment: The index of the memory segment for which the information is required.

        Returns:
            The offset time, in seconds.
        """
        time = c_int64()
        time_units = c_uint32()
        self._f("GetTriggerTimeOffset64", self._handle, byref(time), byref(time_units), segment)
        return time.value * _TimeUnits.to_float(time_units.value)

    def get_unit_info(self, info: PicoInfo | str | int | None = None, *, prefix: bool = True) -> str:
        """Retrieves information about the PicoScope.

        Args:
            info: The info to get. Can be an enum member name (case insensitive) or value.
                If `None`, retrieves all available information.
            prefix: If `True`, includes the enum member name as a prefix.
                For example, returns `"CAL_DATE: 09Aug16"` if `prefix` is `True` else `"09Aug16"`.

        Returns:
            The requested information from the PicoScope.
        """
        values = [PicoInfo(i) for i in range(11)] if info is None else [to_enum(info, PicoInfo, to_upper=True)]
        if info is None:
            values.append(PicoInfo.IPP_VERSION)

        string = create_string_buffer(32)
        required_size = c_int16()

        out: list[str] = []
        for value in values:
            name = f"{value.name}: " if prefix else ""
            self._f("GetUnitInfo", self._handle, string, len(string), byref(required_size), value)
            out.append(f"{name}{string.value.decode()}")
        return "\n".join(out)

    def get_values(
        self,
        num_samples: int | None = None,
        start: int = 0,
        factor: int = 1,
        mode: RatioMode | str | int = "none",
        segment: int = 0,
    ) -> tuple[int, int]:
        """Get the block-mode data, with or without down sampling, starting at the specified sample number.

        It is used to get the stored data from the driver after data collection has stopped.

        Args:
            num_samples: The number of samples required. If `None`, automatically determine
                the number of samples to retrieve.
            start: A zero-based index that indicates the start point for data collection.
                It is measured in sample intervals from the start of the buffer.
            factor: The down-sampling factor that will be applied to the raw data.
            mode: Which down-sampling mode to use. Can be an enum member name (case insensitive) or value.
            segment: The index of the memory segment where the data is stored.

        Returns:
            The actual number of samples retrieved and a flag that indicate whether
                an over-voltage has occurred on any of the channels. It is a bit field
                with bit 0 denoting Channel A (i.e., `(num_samples, overflow)`).
        """
        overflow = c_int16()
        if num_samples is None:
            if self._num_samples < 0:
                msg = "Must call set_timebase() before get_values() or explicitly specify `num_samples`"
                raise MSLConnectionError(self, msg)
            num_samples = self._num_samples
        n_samples = c_uint32(num_samples)
        mode = to_enum(mode, RatioMode, to_upper=True)
        self._f("GetValues", self._handle, start, byref(n_samples), factor, mode, segment, byref(overflow))
        return n_samples.value, overflow.value

    def get_values_async(
        self,
        callback: PicoTechDataReadyCallback,
        num_samples: int | None = None,
        start: int = 0,
        factor: int = 1,
        mode: RatioMode | str | int = "none",
        segment: int = 0,
    ) -> None:
        """Get data either with or without down sampling, starting at the specified sample number.

        It is used to get the stored data from the scope after data collection has stopped.
        It returns the data to the callback.

        Args:
            callback: A callback function to call when data is ready.
            num_samples: The number of samples required. If `None`, automatically determine the
                number of samples to retrieve.
            start: A zero-based index that indicates the start point for data collection.
                It is measured in sample intervals from the start of the buffer.
            factor: The down-sampling factor that will be applied to the raw data.
            mode: Which down-sampling mode to use. Can be an enum member name (case insensitive) or value.
            segment: The index of the memory segment where the data is stored.
        """
        if num_samples is None:
            if self._num_samples < 0:
                msg = "Must call set_timebase() before get_values_async() or explicitly specify `num_samples`"
                raise MSLConnectionError(self, msg)
            num_samples = self._num_samples
        mode = to_enum(mode, RatioMode, to_upper=True)
        self._f("GetValuesAsync", self._handle, start, num_samples, factor, mode, segment, callback, None)

    def get_values_bulk(
        self,
        from_segment: int = 0,
        to_segment: int | None = None,
        factor: int = 1,
        mode: RatioMode | str | int = "none",
        num_samples: int | None = None,
    ) -> tuple[int, list[int]]:
        """Get waveforms captured using rapid block mode.

        The waveforms must have been collected sequentially and in the same run.

        Args:
            from_segment: The first segment from which the waveform should be retrieved.
            to_segment: The last segment from which the waveform should be retrieved. If `None`,
                the last segment is determined from the number of captures.
            factor: The down-sampling factor that will be applied to the raw data.
            mode: Which down-sampling mode to use. Can be an enum member name (case insensitive) or value.
            num_samples: The number of samples required. If `None`, automatically determine the
                number of samples to retrieve.

        Returns:
            The actual number samples retrieved per capture and a list of overflow bit-mask flags for each capture.
        """
        if num_samples is None:
            if self._num_samples < 0:
                msg = "Must call set_timebase() before get_values_bulk() or explicitly specify `num_samples`"
                raise MSLConnectionError(self, msg)
            num_samples = self._num_samples

        n = self.get_no_of_captures()
        if to_segment is None:
            to_segment = n - 1

        num_segments = to_segment - from_segment + 1
        no_of_samples = c_uint32(num_samples * n)
        overflow = (c_int16 * num_segments)()
        mode = to_enum(mode, RatioMode, to_upper=True)
        self._f("GetValuesBulk", self._handle, byref(no_of_samples), from_segment, to_segment, factor, mode, overflow)
        overflows: list[int] = list(overflow)
        return no_of_samples.value, overflows

    def get_values_overlapped(
        self, start: int = 0, factor: int = 1, mode: RatioMode | str | int = "none", segment: int = 0
    ) -> tuple[int, int]:
        """Allows you to make a deferred data-collection request in block mode.

        The advantage of this function is that the driver makes contact with the scope only once,
        when you call [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block], compared
        with the two contacts that occur when you use the conventional
        [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block],
        [get_values][msl.equipment_resources.picotech.picoscope.PicoScope.get_values] calling sequence.
        This slightly reduces the dead time between successive captures in block mode.

        Args:
            start: A zero-based index that indicates the start point for data collection.
                It is measured in sample intervals from the start of the buffer.
            factor: The down-sampling factor that will be applied to the raw data.
            mode: Which down-sampling mode to use. Can be an enum member name (case insensitive) or value.
            segment: The index of the memory segment where the data is stored.

        Returns:
            The actual number of samples retrieved and a flag that indicate whether
                an over-voltage has occurred on any of the channels. It is a bit field
                with bit 0 denoting Channel A (i.e., `(num_samples, overflow)`).
        """
        no_of_samples = c_uint32()
        overflow = c_int16()
        mode = to_enum(mode, RatioMode, to_upper=True)
        self._f(
            "GetValuesOverlapped", self._handle, start, byref(no_of_samples), factor, mode, segment, byref(overflow)
        )
        return no_of_samples.value, overflow.value

    def get_values_overlapped_bulk(
        self,
        start: int = 0,
        factor: int = 1,
        mode: RatioMode | str | int = "none",
        from_segment: int = 0,
        to_segment: int | None = None,
        num_samples: int | None = None,
    ) -> tuple[int, list[int]]:
        """Allows you to make a deferred data-collection request in block mode.

        The advantage of this function is that the driver makes contact with the scope only once,
        when you call [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block], compared
        with the two contacts that occur when you use the conventional
        [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block],
        [get_values_bulk][msl.equipment_resources.picotech.picoscope.PicoScope.get_values_bulk] calling sequence.
        This slightly reduces the dead time between successive captures in rapid block mode.

        Args:
            start: A zero-based index that indicates the start point for data collection.
                It is measured in sample intervals from the start of the buffer.
            factor: The down-sampling factor that will be applied to the raw data.
            mode: Which down-sampling mode to use. Can be an enum member name (case insensitive) or value.
            from_segment: The first segment from which the waveform should be retrieved.
            to_segment: The last segment from which the waveform should be retrieved. If `None`,
                the last segment is determined from the number of captures.
            num_samples: The number of samples required. If `None`, automatically determine the
                number of samples to retrieve.

        Returns:
            The actual number samples retrieved per capture and a list of overflow bit-mask flags for each capture.
        """
        if num_samples is None:
            if self._num_samples < 0:
                msg = "Must call set_timebase() before get_values_overlapped_bulk() or explicitly specify `num_samples`"
                raise MSLConnectionError(self, msg)
            num_samples = self._num_samples

        n = self.get_no_of_captures()
        if to_segment is None:
            to_segment = n - 1

        num_segments = to_segment - from_segment + 1
        no_of_samples = c_uint32(num_samples * n)
        overflow = (c_int16 * num_segments)()
        mode = to_enum(mode, RatioMode, to_upper=True)
        self._f(
            "GetValuesOverlappedBulk",
            self._handle,
            start,
            byref(no_of_samples),
            factor,
            mode,
            from_segment,
            to_segment,
            byref(overflow),
        )

        overflows: list[int] = list(overflow)
        return no_of_samples.value, overflows

    def get_values_trigger_time_offset_bulk64(
        self, from_segment: int = 0, to_segment: int | None = None
    ) -> list[float]:
        """Get the 64-bit time offsets for waveforms captured in rapid block mode.

        If `from_segment` > `to_segment`, the segment index will wrap from the last segment back to 0.

        Args:
            from_segment: The zero-based number of the first segment of interest.
            to_segment: The zero-based number of the last segment of interest. If `None`,
                the last segment is determined from the number of captures.

        Returns:
            The trigger time offset, in seconds, for each requested segment index.
        """
        if to_segment is None:
            to_segment = self.get_no_of_captures() - 1
        n = to_segment - from_segment + 1
        times = (c_int64 * n)()
        units = (c_uint32 * n)()
        self._f("GetValuesTriggerTimeOffsetBulk64", self._handle, times, units, from_segment, to_segment)
        tu = [_TimeUnits(u) for u in units]
        return [t * _TimeUnits.to_float(u) for t, u in zip(times, tu)]

    def is_led_flashing(self) -> int:
        """This function reports whether or not the LED is flashing.

        Returns:
            Whether the LED is flashing.
        """
        status = c_int16()
        self._f("IsLedFlashing", self._handle, byref(status))
        return bool(status.value)

    def is_ready(self) -> bool:
        """Check if the PicoScope has collected the requested number of samples.

        This function may be used instead of a callback function to receive data from
        [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block].
        To use this method, pass `None` as the callback parameter in
        [run_block][msl.equipment_resources.picotech.picoscope.PicoScope.run_block].
        You must then poll the driver to see if it has finished collecting the requested samples.

        Returns:
            Whether the PicoScope has collected the requested number of samples.
        """
        ready = c_int16()
        self._f("IsReady", self._handle, byref(ready))
        return bool(ready.value)

    def is_trigger_or_pulse_width_qualifier_enabled(self) -> tuple[bool, bool]:
        """This function discovers whether a trigger, or pulse width triggering, is enabled.

        Returns:
            Whether the trigger is enabled and the pulse-width qualifier is enabled,
            i.e., `(trigger, pwq)`.
        """
        trigger_enabled = c_int16()
        pulse_width_qualifier_enabled = c_int16()
        self._f(
            "IsTriggerOrPulseWidthQualifierEnabled",
            self._handle,
            byref(trigger_enabled),
            byref(pulse_width_qualifier_enabled),
        )
        return bool(trigger_enabled.value), bool(pulse_width_qualifier_enabled.value)

    def maximum_value(self) -> int:
        """Get the maximum ADC value.

        Returns:
            The maximum ADC value.
        """
        value = c_int16()
        self._f("MaximumValue", self._handle, byref(value))
        return value.value

    def memory_segments(self, num_segments: int) -> int:
        """Sets the number of memory segments that the scope will use.

        When the scope is opened, the number of segments defaults to 1, meaning that each
        capture fills the scopes available memory. This function allows you to divide the
        memory into a number of segments so that the scope can store several waveforms
        sequentially.

        Args:
            num_segments: The number of memory segments.

        Returns:
            The number of samples available in each segment. This is the total number over
                all channels, so if two channels or 8-bit digital ports are in use, the number
                of samples available to each channel is divided by 2.
        """
        num_max_samples = c_int32()
        self._f("MemorySegments", self._handle, num_segments, byref(num_max_samples))
        return num_max_samples.value

    def minimum_value(self) -> int:
        """Get the minimum ADC value.

        Returns:
            The minimum ADC value.
        """
        value = c_int16()
        self._f("MinimumValue", self._handle, byref(value))
        return value.value

    def nearest_sample_interval_stateless(
        self, *, flags: ChannelFlags, dt: float, resolution: DeviceResolution | str | int, use_ets: bool = False
    ) -> tuple[int, float]:
        """Get the nearest timebase index and sample interval for the proposed configuration.

        It does not write the configuration to the device.

        Args:
            flags: The proposed combination of enabled channels and ports. To specify multiple
                channels and ports, use the bitwise-OR of the relevant
                [ChannelFlags][msl.equipment_resources.picotech.picoscope.ChannelFlags].
            dt: The proposed sampling interval, in seconds.
            resolution: The resolution mode in which you propose to operate the oscilloscope.
                Can be an enum member name (case insensitive, with or without the "DR_" prefix) or value.
            use_ets: The proposed state of ETS (disabled or enabled).

        Returns:
            The nearest (rounded up) timebase index and sampling interval, in seconds,
                corresponding to the proposed configuration.
        """
        timebase = c_uint32()
        t = c_double()
        r = to_enum(resolution, DeviceResolution, prefix="DR_", to_upper=True)
        self._f("NearestSampleIntervalStateless", self._handle, flags, dt, r, int(use_ets), byref(timebase), byref(t))
        return timebase.value, t.value

    def no_of_streaming_values(self) -> int:
        """Gets the number of samples available after data collection in streaming mode.

        Call it after calling [stop][msl.equipment_resources.picotech.picoscope.PicoScope.stop].

        Returns:
            The number of samples.
        """
        no_of_values = c_uint32()
        self._f("NoOfStreamingValues", self._handle, byref(no_of_values))
        return no_of_values.value

    def ping_unit(self) -> None:
        """Ping the PicoScope.

        This function can be used to check that the already opened device is still
        connected to the USB port and communication is successful.

        Raises [MSLConnectionError][msl.equipment.interfaces.message_based.MSLConnectionError]
        if pinging was not successful.
        """
        self._f("PingUnit", self._handle)

    def query_output_edge_detect(self) -> bool:
        """Whether output edge detection mode is currently enabled.

        The default state is enabled.

        Returns:
            Whether edge detection is enabled.
        """
        state = c_int16()
        self._f("QueryOutputEdgeDetect", self._handle, byref(state))
        return bool(state)

    def run_block(
        self,
        pre_trigger: float = 0.0,
        callback: PicoTechBlockReadyCallback | None = None,
        segment: int = 0,
    ) -> float:
        """Start acquiring samples in block mode.

        Args:
            pre_trigger: The number of seconds before the trigger event to start acquiring samples.
                The value must be &ge; 0.
            callback: An optional callback function to be called when all samples have been acquired.
                (see also, [wait_until_ready][msl.equipment_resources.picotech.picoscope.PicoScope.wait_until_ready]
                and [is_ready][msl.equipment_resources.picotech.picoscope.PicoScope.is_ready]).
            segment: The index of the memory segment to save the samples to.

        Returns:
            The approximate time, in seconds, that the scope will spend acquiring samples.
                This does not include any auto trigger timeout
        """
        if not self._channels:
            msg = "Must call set_channel() to configure all channels before starting a run block"
            raise MSLConnectionError(self, msg)

        if self._sampling_interval < 0 or self._num_samples < 0:
            msg = "Must call set_timebase() before starting a run block"
            raise MSLConnectionError(self, msg)

        if pre_trigger < 0:
            msg = "The pre-trigger value cannot be negative."
            raise ValueError(msg)

        self._pre_trigger = pre_trigger
        n_pre = round(pre_trigger / self._sampling_interval)
        n_post = self._num_samples - n_pre

        if callback is None:  # a dummy callback
            callback = _BlockReady(0, "", None)

        time_ms = c_int32()
        self._f("RunBlock", self._handle, n_pre, n_post, self._timebase_index, byref(time_ms), segment, callback, None)
        return round(time_ms.value * 1e-3, 3)

    def run_streaming(
        self,
        pre_trigger: float = 0.0,
        factor: int = 1,
        mode: RatioMode | str | int = "none",
        *,
        auto_stop: bool = True,
        strict: bool = True,
    ) -> float:
        """Start collecting samples in streaming mode.

        This function tells the oscilloscope to start collecting data in streaming mode. When
        data has been collected from the device it is down sampled if necessary and then
        delivered to the application. Call
        [get_streaming_latest_values][msl.equipment_resources.picotech.picoscope.PicoScope.get_streaming_latest_values]
        to retrieve the data.

        Args:
            pre_trigger: The number of seconds before the trigger event to start acquiring data.
            factor: The down-sampling factor that will be applied to the raw data.
            mode: Which down-sampling mode to use. Can be an enum member name (case insensitive) or value.
            auto_stop: Whether streaming should stop when all of samples have been captured.
            strict: Whether to force the requested and the actual sampling intervals to be equal.

        Returns:
            The actual time interval, in seconds, between samples.
        """
        self.streaming_done = False

        if not self._channels:
            msg = "Must call set_channel() to configure all channels before starting a run streaming"
            raise MSLConnectionError(self, msg)

        if self._sampling_interval < 0 or self._num_samples < 0:
            msg = "Must call set_timebase() before starting a run streaming"
            raise MSLConnectionError(self, msg)

        if pre_trigger < 0:
            msg = "The pre-trigger value cannot be negative."
            raise ValueError(msg)

        self._pre_trigger = pre_trigger

        n_pre = round(pre_trigger / self._sampling_interval)  # don't use self._streaming_sampling_interval
        n_post = self._num_samples - n_pre

        mode = to_enum(mode, RatioMode, to_upper=True)
        interval = c_uint32(self._streaming_sampling_interval)
        self._f(
            "RunStreaming",
            self._handle,
            byref(interval),
            self._streaming_time_units,
            n_pre,
            n_post,
            auto_stop,
            factor,
            mode,
            self._buffer_size,
        )

        time_factor = _TimeUnits.to_float(self._streaming_time_units)
        dt = interval.value * time_factor
        if strict and (interval.value != self._streaming_sampling_interval):
            msg = (
                f"The actual streaming sampling interval is {dt:.6e} seconds, "
                f"requested {self._streaming_sampling_interval * time_factor:.6e} seconds"
            )
            raise MSLConnectionError(self, msg)

        return dt

    def set_auto_trigger(self, wait: float) -> None:
        """Sets up the auto-trigger function.

        The auto-trigger function starts a capture if no trigger event occurs within a
        specified time after a run command has been issued.

        Args:
            wait: The number of seconds to wait for a trigger before timing out.
                If this argument is zero, the scope will wait indefinitely for a trigger.
                Rounds to the nearest microsecond.
        """
        self._f("SetAutoTriggerMicroSeconds", self._handle, round(wait * 1e6))

    def set_channel(
        self,
        channel: Channel | str | int,
        *,
        bandwidth: BandwidthLimiter | str | int = "full",
        coupling: Coupling | str | int = "dc",
        enabled: bool = True,
        offset: float = 0.0,
        range: Range | str | int = "10V",  # noqa: A002
    ) -> None:
        """Configure a channel.

        Args:
            channel: The channel to configure. Can be an enum member name (case insensitive) or value.
            bandwidth: The bandwidth limiter to use. Can be an enum member name (case insensitive, with
                or without the `"BW_"` prefix) or value.
            coupling: The impedance and coupling type. Can be an enum member name (case insensitive) or value.
            enabled: Whether to enable the channel.
            offset: A voltage to add to the input channel before digitization. The allowable range of
                offsets depends on the input range selected for the channel, as obtained from
                [get_analogue_offset][msl.equipment_resources.picotech.picoscope.PicoScope.get_analogue_offset].
            range: The input voltage range. Can be an enum member name (with or without the `"R_"` prefix) or value.
        """
        channel = to_enum(channel, Channel, to_upper=True)
        bandwidth = to_enum(bandwidth, BandwidthLimiter, prefix="BW_", to_upper=True)
        coupling = to_enum(coupling, Coupling, to_upper=True)
        _range = to_enum(range, Range, prefix="R_")

        # If range=MAX, the SDK uses the maximum enum value and not the maximum range that
        # the PicoScope supports. Here, we choose the maximum supported range.
        if _range == Range.R_MAX:
            _range = Range(self.get_channel_information(channel, info=ChannelInfo.RANGES)[-1])

        self._f("SetChannel", self._handle, channel, enabled, coupling, _range, offset)
        self._f("SetBandwidthFilter", self._handle, channel, bandwidth)

        # Get the voltage range as a floating-point number
        match = re.search(r"(?P<value>\d+)", _range.name)
        assert match is not None  # noqa: S101
        voltage_range = float(match["value"])
        if _range.name.endswith("mV"):
            voltage_range *= 1e-3

        self._channels[channel.name] = ChannelSettings(
            channel=channel,
            enabled=bool(enabled),
            coupling=coupling,
            voltage_range=_range,
            voltage_offset=offset,
            bandwidth=bandwidth,
            max_adu_value=self.maximum_value(),
        )

    def set_data_buffer(
        self,
        channel: Channel | str | int,
        buffer: NDArray[np.int16] | None = None,
        mode: RatioMode | str | int = "none",
        segment: int = 0,
    ) -> None:
        """Set the data buffer for the specified channel.

        Args:
            channel: The channel. Can be an enum member name (case insensitive) or value.
            buffer: A numpy array of dtype [int16][numpy.int16]. If `None` then use a pre-allocated array.
            mode: The ratio mode. Can be an enum member name (case insensitive) or value.
            segment: The index of the memory segment where the data is stored.
        """
        ch = to_enum(channel, Channel, to_upper=True)
        mode = to_enum(mode, RatioMode, to_upper=True)
        if buffer is None:
            if ch.name not in self._channels:
                msg = (
                    f"Must call set_channel(channel='{ch.name}', ...) before setting the data buffer "
                    f"or specify which buffer to use"
                )
                raise MSLConnectionError(self, msg)

            if self._num_samples < 0:
                msg = "Must call set_timebase() before setting the data buffer or specify which buffer to use"
                raise MSLConnectionError(self, msg)

            self.channel[ch.name].allocate(num_samples=self._num_samples, num_captures=self._num_captures)
            buffer = self.channel[ch.name].buffer
            self._buffer_size = buffer.size

        self._f("SetDataBuffer", self._handle, ch, buffer, buffer.size, segment, mode)

    def set_data_buffers(
        self,
        channel: Channel | str | int,
        buffer_max: NDArray[np.int16] | None = None,
        buffer_min: NDArray[np.int16] | None = None,
        mode: RatioMode | str | int = "none",
        segment: int = 0,
    ) -> None:
        """Set the location of one or two buffers for receiving data.

        Args:
            channel: The channel. Can be an enum member name (case insensitive) or value.
            buffer_max: A user-allocated buffer to receive the maximum data values in aggregation mode,
                or the non-aggregated values otherwise. Each value is a 16-bit ADC count scaled
                according to the selected voltage range for the `channel`.
            buffer_min: A user-allocated buffer to receive the minimum data values in aggregation mode.
                Not normally used in other modes, but you can direct the driver to write non-aggregated
                values to this buffer by setting `buffer_max` to `None`.
            mode: The ratio mode. Can be an enum member name (case insensitive) or value.
            segment: The index of the memory segment where the data is stored.
        """
        ch = to_enum(channel, Channel, to_upper=True)
        mode = to_enum(mode, RatioMode, to_upper=True)
        if buffer_min is None:
            if ch.name not in self._channels:
                msg = f"Must call set_channel(channel='{ch.name}', ...) before setting the data buffers"
                raise MSLConnectionError(self, msg)
            buffer_min = self.channel[ch.name].buffer

        if buffer_max is not None and buffer_max.size != buffer_min.size:
            msg = f"The size of buffer_max, {buffer_max.size}, and buffer_min, {buffer_min.size} are not equal"
            raise ValueError(msg)

        self._buffer_size = buffer_min.size
        self._f("SetDataBuffers", self._handle, ch, buffer_max, buffer_min, buffer_min.size, segment, mode)

    def set_device_resolution(self, bit_depth: DeviceResolution | str | int) -> None:
        """Set the device resolution.

        Args:
            bit_depth: The resolution. Can be an enum member name (case insensitive,
                with or without the `"DR_"` prefix) or value.
        """
        resolution = to_enum(bit_depth, DeviceResolution, prefix="DR_", to_upper=True)
        self._f("SetDeviceResolution", self._handle, resolution)

    def set_digital_port(self, port: Channel | str | int, logic_level: int, *, enabled: bool = True) -> None:
        """Enable the digital port and set the logic level.

        Args:
            port: A digital channel. Can be an enum member name (case insensitive) or value.
            logic_level: The voltage at which the state transitions from 0 to 1.
            enabled: Whether to enable or disable the `port`.
        """
        self._f("SetDigitalPort", self._handle, port, enabled, logic_level)

    def set_ets(self, mode: ETSMode | str | int, cycles: int, interleave: int) -> float:
        """Enable or disable ETS (equivalent-time sampling) and set the ETS parameters.

        Args:
            mode: The ETS mode. Can be an enum member name (case insensitive) or value.
            cycles: The number of ETS cycles to store.
            interleave: The number of waveforms to combine into a single ETS capture.

        Returns:
            The effective sampling interval, in seconds, of the ETS data.
        """
        mode = to_enum(mode, ETSMode, to_upper=True)
        sample_time_picoseconds = c_int32()
        self._f("SetEts", self._handle, mode, cycles, interleave, byref(sample_time_picoseconds))
        dt = sample_time_picoseconds.value * 1e-12
        self._sampling_interval = dt
        return dt

    def set_ets_time_buffer(self, buffer: NDArray[np.int64]) -> None:
        """Set the ETS time buffers.

        This function tells the driver where to find your applications ETS time buffers. These
        buffers contain the timing information for each ETS sample after you run a block-mode
        ETS capture.

        Args:
            buffer: A numpy array of dtype [int64][numpy.int64] where each element represents the
                time, in femtoseconds, at which the samples were captured.
        """
        self._f("SetEtsTimeBuffer", self._handle, buffer, len(buffer))

    def set_no_of_captures(self, n: int) -> None:
        """Sets the number of captures to be collected in one run of rapid block mode.

        If you do not call this function before a run, the driver will capture only one
        waveform. Once a value has been set, the value remains constant unless changed.

        Args:
            n: The number of captures.
        """
        self._num_captures = n
        self._f("SetNoOfCaptures", self._handle, n)

    def set_output_edge_detect(self, *, enable: bool) -> None:
        """Enables or disables output edge detection mode for the logic trigger.

        Output edge detection is enabled by default and should be left enabled for normal operation.

        Args:
            enable: Whether to enable or disable output edge detection mode.
        """
        self._f("SetOutputEdgeDetect", self._handle, int(enable))

    def set_pulse_width_digital_port_properties(self, directions: Sequence[DigitalChannelDirections]) -> None:
        """Set the individual digital channels' pulse-width trigger directions.

        Args:
            directions: The digital-port properties. The sequence can contain a single element describing
                the properties of one digital channel, or a number of elements describing several digital
                channels. If empty, digital pulse width triggering is switched off. A digital channel that
                is not included in the array will be set to `DONT_CARE`.
        """
        c_array = (DigitalChannelDirections * len(directions))(*directions)
        self._f("SetPulseWidthDigitalPortProperties", self._handle, c_array, len(directions))

    def set_pulse_width_qualifier_conditions(
        self, conditions: Sequence[Condition], info: ConditionsInfo | str | int
    ) -> None:
        """Set the condition to the pulse-width qualifier.

        It can either add the new condition to the existing qualifier, or clear the
        existing qualifier and replace it with the new condition.

        Args:
            conditions: A sequence of conditions.
            info: Whether to add this condition to the existing definition or clear the definition
                and start a new one. Can be an enum member name (case insensitive) or value.
        """
        c_array = (Condition * len(conditions))(*conditions)
        info = to_enum(info, ConditionsInfo, to_upper=True)
        self._f("SetPulseWidthQualifierConditions", self._handle, c_array, len(conditions), info)

    def set_pulse_width_qualifier_directions(self, directions: Sequence[Direction]) -> None:
        """Set the directions for all the trigger sources used with the pulse-width qualifier.

        Args:
            directions: Specifies which direction to apply to each trigger source.
        """
        c_array = (Direction * len(directions))(*directions)
        self._f("SetPulseWidthQualifierDirections", self._handle, c_array, len(directions))

    def set_pulse_width_qualifier_properties(
        self,
        lower: int,
        upper: int = 0,
        type: PulseWidthType | str | int = "none",  # noqa: A002
    ) -> None:
        """Set the pulse width timings and logic type of the pulse-width trigger qualifier.

        Args:
            lower: The lower limit of the pulse-width counter, in samples. This argument is
                required for all pulse width types.
            upper: The upper limit of the pulse-width counter, in samples. This argument is
                used only when the type is `IN_RANGE` or `OUT_OF_RANGE`.
            type: The type of pulse width trigger. Can be an enum member name (case insensitive) or value.
        """
        typ = to_enum(type, PulseWidthType, to_upper=True)
        self._f("SetPulseWidthQualifierProperties", self._handle, lower, upper, typ)

    def set_sig_gen_arbitrary(  # noqa: PLR0913
        self,
        waveform: NDArray[np.float64],
        repetition_rate: float | None = None,
        offset_voltage: float = 0.0,
        peak_to_peak: float | None = None,
        start_delta_phase: int | None = None,
        stop_delta_phase: int | None = None,
        delta_phase_increment: int = 0,
        dwell_count: int | None = None,
        sweep_type: SweepType | str | int = "up",
        operation: ExtraOperations | str | int = "off",
        index_mode: IndexMode | str | int = "single",
        shots: int = 0,
        sweeps: int = 0,
        trigger_type: SigGenTrigType | str | int = "rising",
        trigger_source: SigGenTrigSource | str | int = "none",
        ext_in_threshold: int = 0,
    ) -> NDArray[np.int16]:
        """Set the signal generator to produce an arbitrary waveform.

        Args:
            waveform: The arbitrary waveform, in volts. Must be 1D array.
            repetition_rate: The requested repetition rate (frequency in Hz) of the entire arbitrary waveform.
                The actual repetition rate that is used may be different based on the specifications of
                the AWG. If specified then the
                [sig_gen_frequency_to_phase][msl.equipment_resources.picotech.picoscope.PicoScope.sig_gen_frequency_to_phase]
                method is called (with the `mode` value) to determine the value of `start_delta_phase`.
            offset_voltage: The offset, in volts, to be applied to the waveform.
            peak_to_peak: The peak-to-peak voltage of the waveform signal. If `None`, uses
                the maximum value of the `waveform` to determine the peak-to-peak voltage.
            start_delta_phase: The initial value added to the phase accumulator as the generator begins
                to step through the waveform buffer. If `None` then `repetition_rate` must be specified.
            stop_delta_phase: The final value added to the phase accumulator before the generator restarts or
                reverses the sweep. When frequency sweeping is not required, set equal to `start_delta_phase`
                (which is what it is set to if `None`).
            delta_phase_increment: The amount added to the delta phase value every time the `dwell_count`
                period expires. This determines the amount by which the generator sweeps the output frequency
                in each dwell period. When frequency sweeping is not required, set to zero.
            dwell_count: The time, in 50 ns steps, between successive additions of `delta_phase_increment` to the
                delta phase accumulator. This determines the rate at which the generator sweeps the output frequency.
                If `None`, the minimum dwell count value is used.
            sweep_type: How the frequency will sweep from `start_delta_phase` to `stop_delta_phase`
                or in the opposite direction. Can be an enum member name (case insensitive) or value.
            operation: The type of waveform to be produced. Can be an enum member name (case insensitive) or value.
            index_mode: Specifies how the signal will be formed from the arbitrary waveform data.
                Can be an enum member name (case insensitive) or value.
            shots: See the manual.
            sweeps: See the manual.
            trigger_type: The type of trigger that will be applied to the signal generator.
                Can be an enum member name (case insensitive) or value.
            trigger_source: The source that will trigger the signal generator.
                Can be an enum member name (case insensitive) or value.
            ext_in_threshold: Used to set trigger level for an external trigger.

        Returns:
            The arbitrary waveform in ADU counts.
        """
        _, max_value, min_size, max_size = self.sig_gen_arbitrary_min_max_values()
        if waveform.size < min_size:
            msg = f"The waveform size is {waveform.size}, must be >= {min_size}"
            raise ValueError(msg)
        if waveform.size > max_size:
            msg = f"The waveform size is {waveform.size}, must be <= {max_size}"
            raise ValueError(msg)

        sweep_typ = to_enum(sweep_type, SweepType, to_upper=True)
        extra_ops = to_enum(operation, ExtraOperations, to_upper=True)
        index_mode = to_enum(index_mode, IndexMode, to_upper=True)
        trig_typ = to_enum(trigger_type, SigGenTrigType, to_upper=True)
        trig_source = to_enum(trigger_source, SigGenTrigSource, to_upper=True)

        if start_delta_phase is None and repetition_rate is None:
            msg = "Must specify either 'start_delta_phase' or 'repetition_rate'"
            raise ValueError(msg)

        if start_delta_phase is None:
            assert repetition_rate is not None  # noqa: S101
            start_delta_phase = self.sig_gen_frequency_to_phase(repetition_rate, index_mode, waveform.size)

        if stop_delta_phase is None:
            stop_delta_phase = start_delta_phase

        if dwell_count is None:
            dwell_count = to_enum("MIN_DWELL_COUNT", _Constants, prefix=f"{self._prefix}_", to_upper=True)

        # convert the waveform from volts to analogue-to-digital units
        _waveform = waveform.copy()
        max_waveform_value: float = np.max(np.absolute(_waveform))
        _waveform /= max_waveform_value  # the waveform must be within the range -1.0 to 1.0
        _waveform *= max_value
        waveform_adu: NDArray[np.int16] = _waveform.round(out=_waveform).astype(np.int16)

        if peak_to_peak is None:
            peak_to_peak = max_waveform_value / 2.0

        offset = round(offset_voltage * 1e6)
        pk2pk = round(peak_to_peak * 1e6)

        self._f(
            "SetSigGenArbitrary",
            self._handle,
            offset,
            pk2pk,
            start_delta_phase,
            stop_delta_phase,
            delta_phase_increment,
            dwell_count,
            waveform_adu,
            waveform_adu.size,
            sweep_typ,
            extra_ops,
            index_mode,
            shots,
            sweeps,
            trig_typ,
            trig_source,
            ext_in_threshold,
        )
        return waveform_adu

    def set_sig_gen_builtin_v2(  # noqa: PLR0913
        self,
        offset_voltage: float = 0.0,
        peak_to_peak: float = 1.0,
        wave_type: WaveType | str | int = "sine",
        start_frequency: float = 1.0,
        stop_frequency: float | None = None,
        increment: float = 0.1,
        dwell_time: float = 1.0,
        sweep_type: SweepType | str | int = "up",
        operation: ExtraOperations | str | int = "off",
        shots: int = 0,
        sweeps: int = 0,
        trigger_type: SigGenTrigType | str | int = "rising",
        trigger_source: SigGenTrigSource | str | int = "none",
        ext_in_threshold: int = 0,
    ) -> None:
        """Set up the signal generator to produce a signal from a list of built-in waveforms.

        Args:
            offset_voltage: The voltage offset, in volts, to be applied to the waveform.
            peak_to_peak: The peak-to-peak voltage, in volts, of the waveform signal.
            wave_type: The type of waveform to be generated.
                Can be an enum member name (case insensitive) or value.
            start_frequency: The frequency that the signal generator will initially produce.
            stop_frequency: The frequency at which the sweep reverses direction or returns
                to the initial frequency. If `None`, it is set equal to `start_frequency`.
            increment: The amount of frequency increase or decrease in sweep mode.
            dwell_time: The time, in seconds, for which the sweep stays at each frequency.
            sweep_type: How the frequency will sweep from `start_frequency` to `stop_frequency`
                or in the opposite direction. Can be an enum member name (case insensitive) or value.
            operation: The type of waveform to be produced (not used by 5000A models).
                Can be an enum member name (case insensitive) or value.
            shots: See the manual.
            sweeps: See the manual.
            trigger_type: The type of trigger that will be applied to the signal generator.
                Can be an enum member name (case insensitive) or value.
            trigger_source: The source that will trigger the signal generator.
                Can be an enum member name (case insensitive) or value.
            ext_in_threshold: Used to set trigger level for an external trigger.
        """
        wave_typ = to_enum(wave_type, WaveType, to_upper=True)
        sweep_typ = to_enum(sweep_type, SweepType, to_upper=True)
        extra_ops = to_enum(operation, ExtraOperations, to_upper=True)
        trig_typ = to_enum(trigger_type, SigGenTrigType, to_upper=True)
        trig_source = to_enum(trigger_source, SigGenTrigSource, to_upper=True)

        if stop_frequency is None:
            stop_frequency = start_frequency

        self._f(
            "SetSigGenBuiltInV2",
            self._handle,
            round(offset_voltage * 1e6),
            round(peak_to_peak * 1e6),
            wave_typ,
            start_frequency,
            stop_frequency,
            increment,
            dwell_time,
            sweep_typ,
            extra_ops,
            shots,
            sweeps,
            trig_typ,
            trig_source,
            ext_in_threshold,
        )

    def set_timebase(self, dt: float, duration: float, segment: int = 0) -> tuple[float, int]:
        """Set the timebase information.

        This method does not consider ETS (equivalent-time sampling). If using ETS, consider using
        [set_ets][msl.equipment_resources.picotech.picoscope.PicoScope.set_ets]. See also,
        [nearest_sample_interval_stateless][msl.equipment_resources.picotech.picoscope.PicoScope.nearest_sample_interval_stateless].

        Args:
            dt: The requested sampling interval, in seconds.
            duration: The number of seconds to acquire samples for.
            segment: The index of the memory segment to use.

        Returns:
            The actual sampling interval (i.e., actual &Delta;t) and the number of samples
                that will be acquired.
        """
        self._timebase_index = round(self._get_timebase_index(float(dt)))
        num_samples_requested = round(duration / dt)
        self._sampling_interval, _ = self.get_timebase2(self._timebase_index, num_samples_requested, segment)

        self._num_samples = round(duration / self._sampling_interval)

        # determine the TimeUnits enum from the sample interval
        for unit in _TimeUnits:
            num_seconds_float = self._sampling_interval / _TimeUnits.to_float(unit)
            if num_seconds_float < 1e9:  # use <9 digits to specify the streaming sampling interval  # noqa: PLR2004
                self._streaming_sampling_interval = round(num_seconds_float)
                self._streaming_time_units = unit
                break

        return self._sampling_interval, self._num_samples

    def set_trigger(
        self,
        channel: Channel | str | int,
        threshold: float,
        *,
        delay: float = 0.0,
        direction: ThresholdDirection | str | int = "RISING",
        timeout: float | None = None,
        enable: bool = True,
    ) -> None:
        """Set up the trigger.

        Args:
            channel: The trigger channel. Can be an enum member name (case insensitive) or value.
            threshold: The threshold voltage to signal a trigger event.
            delay: The time, in seconds, between the trigger occurring and the first sample.
            direction: The direction in which the signal must move to cause a trigger.
                Can be an enum member name (case insensitive) or value.
            timeout: The time, in seconds, to wait to automatically create a trigger event if no
                trigger event occurs. If `timeout` &le; 0 or `None`, then wait indefinitely for a trigger.
                Only accurate to the nearest millisecond.
            enable: Set to `False` to disable the trigger for this channel.
        """
        ch = to_enum(channel, Channel, to_upper=True)
        if ch.name not in self._channels:
            msg = f"Must call set_channel(channel='{ch.name}', ...) before enabling a trigger with channel {ch.name}"
            raise MSLConnectionError(self, msg)

        if self._sampling_interval < 0:
            msg = "Must call set_timebase() before setting the trigger"
            raise MSLConnectionError(self, msg)

        if delay < 0:
            msg = f"The trigger delay must be >=0 seconds, requested a delay of {delay} seconds"
            raise ValueError(msg)

        delay_ = round(delay / self._sampling_interval)
        max_delay_count = to_enum("MAX_DELAY_COUNT", _Constants, prefix=f"{self._prefix}_", to_upper=True)
        if delay_ > max_delay_count:
            msg = (
                f"The maximum allowed trigger delay is {max_delay_count * self._sampling_interval} seconds, "
                f"requested a delay of {delay} seconds"
            )
            raise ValueError(msg)

        if ch == Channel.EXT:
            max_value = to_enum("EXT_MAX_VALUE", _Constants, prefix=f"{self._prefix}_", to_upper=True)
            max_volts = to_enum("EXT_MAX_VOLTAGE", _Constants, prefix=f"{self._prefix}_", to_upper=True)
            threshold_adu = round(max_value * threshold / float(max_volts))
        else:
            voltage_offset = self._channels[ch.name].voltage_offset
            adu_per_volt = 1.0 / self._channels[ch.name].volts_per_adu
            threshold_adu = round(adu_per_volt * (threshold + voltage_offset))

        trig_dir = to_enum(direction, ThresholdDirection, to_upper=True)
        auto_trigger_ms = round(max(0, timeout * 1e3)) if timeout is not None else 0
        self._f("SetSimpleTrigger", self._handle, enable, ch, threshold_adu, trig_dir, delay_, auto_trigger_ms)

    def set_trigger_channel_conditions_v2(
        self, conditions: Sequence[Condition], info: ConditionsInfo | str | int
    ) -> None:
        """Sets up trigger conditions on the scope's inputs.

        Args:
            conditions: The conditions that should be applied to each channel. In the simplest case,
                the sequence consists of a single element. When there is more than one element, the
                overall trigger condition is the logical OR of all the elements.
            info: Specifies whether to clear the existing conditions or add the current condition to
                them using logical OR. Can be an enum member name (case insensitive) or value.
        """
        c_array = (Condition * len(conditions))(*conditions)
        info = to_enum(info, ConditionsInfo, to_upper=True)
        self._f("SetTriggerChannelConditionsV2", self._handle, c_array, len(conditions), info)

    def set_trigger_channel_directions_v2(self, directions: Sequence[Direction]) -> None:
        """Sets the direction of the trigger for each channel.

        Args:
            directions: A sequence of directions in which the signal must pass through
                the threshold to activate the trigger.
        """
        c_array = (Direction * len(directions))(*directions)
        self._f("SetTriggerChannelDirectionsV2", self._handle, c_array, len(directions))

    def set_trigger_channel_properties_v2(self, properties: Sequence[TriggerChannelPropertiesV2]) -> None:
        """Enable or disable triggering and set its parameters.

        Args:
            properties: The requested properties. The sequence can contain a single element describing the
                properties of one channel, or a number of elements describing several channels. If empty,
                triggering is switched off.
        """
        c_array = (TriggerChannelPropertiesV2 * len(properties))(*properties)
        self._f("SetTriggerChannelPropertiesV2", self._handle, c_array, len(properties), 0)

    def set_trigger_delay(self, delay: float) -> None:
        """Sets the post-trigger delay, which causes capture to start a defined time after the trigger event.

        Args:
            delay: The time, in seconds, between the trigger occurring and the first sample
        """
        if self._sampling_interval < 0:
            msg = "Must call set_timebase() before setting the trigger delay"
            raise MSLConnectionError(self, msg)

        delay_ = round(delay / self._sampling_interval)
        max_delay_count = to_enum("MAX_DELAY_COUNT", _Constants, prefix=f"{self._prefix}_", to_upper=True)
        if delay_ > max_delay_count:
            msg = (
                f"The maximum allowed trigger delay is {max_delay_count * self._sampling_interval} seconds, "
                f"requested a delay of {delay} seconds"
            )
            raise ValueError(msg)

        self._f("SetTriggerDelay", self._handle, delay_)

    def set_trigger_digital_port_properties(self, directions: Sequence[DigitalChannelDirections]) -> None:
        """Set the individual digital channel's trigger directions.

        Args:
            directions: The digital-port properties. The sequence can contain a single element describing
                the properties of one digital channel, or a number of elements describing several digital
                channels. If empty, digital pulse width triggering is switched off. A digital channel that
                is not included in the array will be set to `DONT_CARE`. The outcomes of all the `directions`
                in the sequence are bitwise-OR'ed together to produce the final trigger signal.
        """
        c_array = (DigitalChannelDirections * len(directions))(*directions)
        self._f("SetTriggerDigitalPortProperties", self._handle, c_array, len(directions))

    def sig_gen_arbitrary_min_max_values(self) -> tuple[int, int, int, int]:
        """Get the range of possible sample values and waveform buffer sizes.

        Returns:
            The range of possible sample values and waveform buffer sizes that can be supplied to
                [set_sig_gen_arbitrary][msl.equipment_resources.picotech.picoscope.PicoScope.set_sig_gen_arbitrary]
                for setting up the arbitrary waveform generator (i.e., `(min_value, max_value, min_size, max_size)`).
        """
        min_value = c_int16()
        max_value = c_int16()
        min_size = c_uint32()
        max_size = c_uint32()
        self._f(
            "SigGenArbitraryMinMaxValues",
            self._handle,
            byref(min_value),
            byref(max_value),
            byref(min_size),
            byref(max_size),
        )
        return min_value.value, max_value.value, min_size.value, max_size.value

    def sig_gen_frequency_to_phase(self, repetition_rate: float, index_mode: IndexMode | str | int, size: int) -> int:
        """Converts a frequency to a phase count for use with the arbitrary waveform generator (AWG).

        Args:
            repetition_rate: The requested repetition rate (frequency in Hz) of the entire arbitrary waveform.
            index_mode: Specifies how the signal will be formed from the arbitrary waveform data.
                Can be an enum member name (case insensitive) or value.
            size: The size (number of samples) of the waveform.

        Returns:
            The phase count. The phase count can then be sent to the driver through
                [set_sig_gen_arbitrary][msl.equipment_resources.picotech.picoscope.PicoScope.set_sig_gen_arbitrary].
        """
        mode = to_enum(index_mode, IndexMode, to_upper=True)

        phase = c_uint32()
        self._f("SigGenFrequencyToPhase", self._handle, repetition_rate, mode, size, byref(phase))
        if phase.value < 1:
            msg = "The delta phase value is < 1, increase the repetition rate value"
            raise ValueError(msg)
        return phase.value

    def sig_gen_software_control(self, *, state: bool) -> None:
        """Send a software trigger event, or starts and stops gating.

        Args:
            state: Specifies the new state of the gate signal.
        """
        self._f("SigGenSoftwareControl", self._handle, int(state))

    def stop(self) -> None:
        """Stop the oscilloscope from sampling data.

        If this function is called before a trigger event occurs, then the
        oscilloscope may not contain valid data.
        """
        self._f("Stop", self._handle)

    def trigger_within_pre_trigger_samples(self, state: TriggerWithinPreTrigger | str | int) -> None:
        """Allow a trigger anywhere within the pre-trigger samples.

        This function selects a mode in which the scope can be triggered anywhere within the pre-trigger
        samples, as opposed to the normal operation of only arming the trigger after all the pre-trigger
        samples have been collected.

        Args:
            state: Can be an enum member name (case insensitive) or value.
        """
        state = to_enum(state, TriggerWithinPreTrigger, to_upper=True)
        self._f("TriggerWithinPreTriggerSamples", self._handle, state)

    def wait_until_ready(self) -> None:
        """Blocking function to wait for the scope to finish acquiring samples."""
        while not self.is_ready():
            time.sleep(0.01)


_BlockReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_void_p)
"""A callback function when the data block is ready."""

_DataReady = FUNCTYPE(None, c_int16, PICO_STATUS, c_uint32, c_int16, c_void_p)
"""A callback function when the data is ready."""

_StreamingReady = FUNCTYPE(None, c_int16, c_int32, c_uint32, c_int16, c_uint32, c_int16, c_int16, c_void_p)
"""A callback function when the data stream is ready."""


def block_ready(f: PicoTechBlockReadyCallback) -> _CFunctionType:
    """Use as a decorator for a callback function when the data block is ready.

    See [ps5000a_block_ready_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/picotech/ps5000a_block_ready_callback.py)
    for an example usage.
    """
    return _BlockReady(f)


def data_ready(f: PicoTechDataReadyCallback) -> _CFunctionType:
    """Use as a decorator for a callback function when the data is ready.

    See [ps5000a_data_ready_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/picotech/ps5000a_data_ready_callback.py)
    for an example usage.
    """
    return _DataReady(f)


def streaming_ready(f: PicoTechStreamingReadyCallback) -> _CFunctionType:
    """Use as a decorator for a callback function when the data stream is ready.

    See [ps5000a_streaming_ready_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/picotech/ps5000a_streaming_ready_callback.py)
    for an example usage.
    """
    return _StreamingReady(f)


class _Constants(IntEnum):
    PS2000A_MIN_DWELL_COUNT = 3
    PS2000A_EXT_MAX_VALUE = 32767

    PS3000A_MIN_DWELL_COUNT = 3
    PS3000A_EXT_MAX_VALUE = 32767

    PS4000A_MAX_DELAY_COUNT = 8388607
    PS4000A_MIN_DWELL_COUNT = 10
    PS4000A_EXT_MAX_VALUE = 32767

    PS5000A_MAX_DELAY_COUNT = 8388607
    PS5000A_MIN_DWELL_COUNT = 3
    PS5000A_EXT_MAX_VALUE = 32767
    PS5000A_EXT_MAX_VOLTAGE = 5


class ChannelSettings:
    """The settings for a channel."""

    def __init__(
        self,
        *,
        bandwidth: BandwidthLimiter,
        channel: Channel,
        enabled: bool,
        coupling: Coupling,
        voltage_range: float,
        voltage_offset: float,
        max_adu_value: int,
    ) -> None:
        """Information about a PicoScope channel.

        Do not instantiate this class directly. Created when
        [set_channel][msl.equipment_resources.picotech.picoscope.PicoScope.set_channel]
        is called.

        Args:
            channel: The channel.
            bandwidth: The bandwidth limiter that is used.
            enabled: Whether the channel is enabled.
            coupling: The impedance and coupling type.
            voltage_range: The voltage range, in Volts.
            voltage_offset: The voltage offset, in Volts.
            max_adu_value: The maximum analogue-to-digital value.
        """
        self.channel: Channel = channel
        """The channel."""

        self.enabled: bool = enabled
        """Whether the channel is enabled."""

        self.bandwidth: BandwidthLimiter = bandwidth
        """The bandwidth limiter that is used."""

        self.coupling: Coupling = coupling
        """The impedance and coupling type."""

        self.voltage_range: float = voltage_range
        """The voltage range, in Volts."""

        self.voltage_offset: float = voltage_offset
        """The voltage offset, in Volts."""

        self.volts_per_adu: float = voltage_range / float(max_adu_value)
        """The voltage/ADU factor."""

        # the raw data in analogue-to-digital units
        self._adu_values: NDArray[np.int16] = np.empty((0, 0), dtype=np.int16)

    @property
    def adu(self) -> NDArray[np.int16]:
        """The samples in ADU counts."""
        return self._adu_values

    @property
    def buffer(self) -> NDArray[np.int16]:
        """An alias for the samples in ADU counts."""
        return self._adu_values

    @property
    def volts(self) -> NDArray[np.floating]:
        """The samples in volts."""
        # From the manual, the voltage offset gets added to the input channel before digitization.
        # Must convert the ADU values to volts and then subtract the offset.
        return (self._adu_values * self.volts_per_adu) - self.voltage_offset

    @property
    def num_samples(self) -> int:
        """The number of samples to acquire for this channel."""
        return self._adu_values.size

    def allocate(self, num_samples: int, num_captures: int = 1) -> None:
        """Maybe allocate memory to save the samples (if the array needs to be resized).

        Args:
            num_samples: The number of samples.
            num_captures: The number of captures.
        """
        if self._adu_values.size != num_captures * num_samples:
            if num_captures == 1:
                self._adu_values = np.empty(num_samples, dtype=np.int16)
            else:
                self._adu_values = np.empty((num_captures, num_samples), dtype=np.int16)


class DeviceResolution(IntEnum):
    """Resolution of the sampling hardware in the oscilloscope.

    Attributes:
        DR_8BIT (int): `0`
        DR_12BIT (int): `1`
        DR_14BIT (int): `2`
        DR_15BIT (int): `3`
        DR_16BIT (int): `4`
    """

    DR_8BIT = 0
    DR_12BIT = 1
    DR_14BIT = 2
    DR_15BIT = 3
    DR_16BIT = 4


class ExtraOperations(IntEnum):
    """Additional signal types for the signal generator.

    Attributes:
        OFF (int): Normal signal generator operation. `0`
        WHITENOISE (int): Produces white noise. `1`
        PRBS (int): Produces a pseudo-random binary sequence. `2`
    """

    OFF = 0
    WHITENOISE = 1
    PRBS = 2


class BandwidthLimiter(IntEnum):
    """The hardware bandwidth limiter fitted to each analogue input channel.

    Attributes:
        BW_FULL (int): Use the scope's full specified bandwidth. `0`
        BW_20MHZ (int): Enable the hardware 20 MHz bandwidth limiter. `1`
    """

    BW_FULL = 0
    BW_20MHZ = 1


class Coupling(IntEnum):
    """Input coupling modes for each analogue channel.

    Attributes:
        AC (int): AC coupling. `0`
        DC (int): DC coupling. `1`
    """

    AC = 0
    DC = 1


class Channel(IntEnum):
    """An analogue input channel, 8-bit digital port or other input.

    Attributes:
        A (int): Analogue channel A. `0`
        B (int): Analogue channel B. `1`
        C (int): Analogue channel C. `2`
        D (int): Analogue channel D. `3`
        EXT (int): External trigger input; not on MSOs. `4`
        MAX_CHANNELS (int): `4`
        TRIGGER_AUX (int): Reserved. `5`
        MAX_TRIGGER_SOURCES (int): `6`
        PORT0 (int): Digital port 0, inputs D0-D7, MSO models only. `0x80`
        PORT1 (int): Digital port 1, inputs D8-D15, MSO models only. `0x81`
        PORT2 (int): Reserved. `0x82`
        PORT3 (int): Reserved. `0x83`
        PULSE_WIDTH_SOURCE (int): Pulse width qualifier. `0x10000000`
    """

    A = 0
    B = 1
    C = 2
    D = 3
    EXT = 4
    MAX_CHANNELS = EXT
    TRIGGER_AUX = 5
    MAX_TRIGGER_SOURCES = 6
    PORT0 = 0x80
    PORT1 = 0x81
    PORT2 = 0x82
    PORT3 = 0x83
    PULSE_WIDTH_SOURCE = 0x10000000


class ChannelFlags(IntFlag):
    """Channel flags enum.

    Attributes:
        A (int): Analogue channel A. `1`
        B (int): Analogue channel B. `2`
        C (int): Analogue channel C. `4`
        D (int): Analogue channel D. `8`
        PORT0 (int): Digital port 0, inputs D0-D7, MSO models only. `0x10000`
        PORT1 (int): Digital port 1, inputs D8-D15, MSO models only. `0x20000`
        PORT2 (int): Reserved. `0x40000`
        PORT3 (int): Reserved. `0x80000`

    """

    A = 1
    B = 2
    C = 4
    D = 8
    PORT0 = 0x10000
    PORT1 = 0x20000
    PORT2 = 0x40000
    PORT3 = 0x80000


class DigitalDirection(IntEnum):
    """The polarity of a digital channel used as a trigger source.

    Attributes:
        DONT_CARE (int): Ignore input. `0`
        LOW (int): Input must be low. `1`
        HIGH (int): Input must be high. `2`
        RISING (int): Input must have a rising edge. `3`
        FALLING (int): Input must have a falling edge. `4`
        RISING_OR_FALLING (int): Input must have an edge of either polarity. `5`
    """

    DONT_CARE = 0
    LOW = 1
    HIGH = 2
    RISING = 3
    FALLING = 4
    RISING_OR_FALLING = 5


class Range(IntEnum):
    """The possible voltage ranges to which an analogue input channel can be set.

    Each range is bipolar, so the `R_10mV` range spans from -10 mV to +10 mV.

    Attributes:
        R_10mV (int): `0`
        R_20mV (int): `1`
        R_50mV (int): `2`
        R_100mV (int): `3`
        R_200mV (int): `4`
        R_500mV (int): `5`
        R_1V (int): `6`
        R_2V (int): `7`
        R_5V (int): `8`
        R_10V (int): `9`
        R_20V (int): `10`
        R_50V (int): `11`
        R_MAX (int): `12`
    """

    R_10mV = 0
    R_20mV = 1
    R_50mV = 2
    R_100mV = 3
    R_200mV = 4
    R_500mV = 5
    R_1V = 6
    R_2V = 7
    R_5V = 8
    R_10V = 9
    R_20V = 10
    R_50V = 11
    R_MAX = 12


class ETSMode(IntEnum):
    """ETS (equivalent-time sampling) mode.

    Attributes:
        OFF (int): ETS disabled. `0`
        FAST (int): Return ready as soon as requested number of interleaves is available. `1`
        SLOW (int): Return ready every time a new set of `no_of_cycles` is collected. `2`
    """

    OFF = 0
    FAST = 1
    SLOW = 2


class _TimeUnits(IntEnum):
    """A unit of time.

    Attributes:
        FS (int): Femtoseconds. `0`
        PS (int): Picoseconds. `1`
        NS (int): Nanoseconds. `2`
        US (int): Microseconds. `3`
        MS (int): Milliseconds. `4`
        S (int): Seconds. `5`
    """

    FS = 0
    PS = 1
    NS = 2
    US = 3
    MS = 4
    S = 5

    @staticmethod
    def to_float(unit: int) -> float:
        """Convert the enum value to a floating-point number in seconds."""
        return 10 ** (3 * unit) * 1e-15


class SweepType(IntEnum):
    """The frequency sweep mode of the signal generator or arbitrary waveform generator.

    Attributes:
        UP (int): Sweep the frequency from lower limit up to upper limit. `0`
        DOWN (int): Sweep the frequency from upper limit down to lower limit. `1`
        UPDOWN (int): Sweep the frequency up and then down. `2`
        DOWNUP (int): Sweep the frequency down and then up. `3`
    """

    UP = 0
    DOWN = 1
    UPDOWN = 2
    DOWNUP = 3


class WaveType(IntEnum):
    """Standard waveform produced by the signal generator.

    Attributes:
        SINE (int): `0`
        SQUARE (int): `1`
        TRIANGLE (int): `2`
        RAMP_UP (int): `3`
        RAMP_DOWN (int): `4`
        SINC (int): `5`
        GAUSSIAN (int): `6`
        HALF_SINE (int): `7`
        DC_VOLTAGE (int): `8`
        WHITE_NOISE (int): `9`
    """

    SINE = 0
    SQUARE = 1
    TRIANGLE = 2
    RAMP_UP = 3
    RAMP_DOWN = 4
    SINC = 5
    GAUSSIAN = 6
    HALF_SINE = 7
    DC_VOLTAGE = 8
    WHITE_NOISE = 9


class ConditionsInfo(IntEnum):
    """Specify what to do with any existing trigger conditions that you have previously set up.

    Attributes:
        CLEAR (int): Clear existing trigger logic and replace with the new condition. `1`
        ADD (int): Add the new condition, using Boolean OR, to the existing trigger logic. `2`
    """

    CLEAR = 0x00000001
    ADD = 0x00000002


class SigGenTrigType(IntEnum):
    """Trigger types used by the signal generator or arbitrary waveform generator.

    Attributes:
        RISING (int): `0`
        FALLING (int): `1`
        GATE_HIGH (int): `2`
        GATE_LOW (int): `3`
    """

    RISING = 0
    FALLING = 1
    GATE_HIGH = 2
    GATE_LOW = 3


class SigGenTrigSource(IntEnum):
    """How triggering of the signal generator or arbitrary waveform generator works.

    Attributes:
        NONE (int): Run without waiting for trigger. `0`
        SCOPE_TRIG (int): Use scope trigger. `1`
        AUX_IN (int): Use AUX input. `2`
        EXT_IN (int): Use EXT input. `3`
        SOFT_TRIG (int): Wait for software trigger from
            [sig_gen_software_control][msl.equipment_resources.picotech.picoscope.PicoScope.sig_gen_software_control].
            `4`
    """

    NONE = 0
    SCOPE_TRIG = 1
    AUX_IN = 2
    EXT_IN = 3
    SOFT_TRIG = 4


class IndexMode(IntEnum):
    """Index mode used by the arbitrary waveform generator.

    Attributes:
        SINGLE (int): The generator outputs the raw contents of the buffer repeatedly.
            This mode is the only one that can generate asymmetrical waveforms. You
            can also use this mode for symmetrical waveforms, but the `DUAL` mode makes
            more efficient use of the buffer memory. `0`
        DUAL (int): The generator outputs the contents of the buffer from beginning to
            end, and then does a second pass in the reverse direction through the buffer.
            This allows you to specify only the first half of a waveform with twofold
            symmetry, such as a Gaussian function, and let the generator fill in the
            other half. `1`
        QUAD (int): Not used. `2`
    """

    SINGLE = 0
    DUAL = 1
    QUAD = 2


class ThresholdMode(IntEnum):
    """The type of threshold used by a trigger condition.

    Attributes:
        LEVEL (int): An edge or level trigger with a single threshold. `0`
        WINDOW (int): Two thresholds defining a range. `1`
    """

    LEVEL = 0
    WINDOW = 1


class ThresholdDirection(IntEnum):
    """The direction(s) in which the trigger source must cross the threshold(s) to cause a trigger event.

    Attributes:
        ABOVE (int): Using upper threshold. `0`
        BELOW (int): Using upper threshold. `1`
        RISING (int): Using upper threshold. `2`
        FALLING (int): Using upper threshold. `3`
        RISING_OR_FALLING (int): Using both thresholds. `4`
        ABOVE_LOWER (int): Using lower threshold. `5`
        BELOW_LOWER (int): Using lower threshold. `6`
        RISING_LOWER (int): Using lower threshold. `7`
        FALLING_LOWER (int): Using lower threshold. `8`
        INSIDE (int): Windowing using both thresholds. `0`
        OUTSIDE (int): Windowing using both thresholds. `1`
        ENTER (int): Windowing using both thresholds. `2`
        EXIT (int): Windowing using both thresholds. `3`
        ENTER_OR_EXIT (int): Windowing using both thresholds. `4`
        POSITIVE_RUNT (int): Windowing using both thresholds. `9`
        NEGATIVE_RUNT (int): Windowing using both thresholds. `10`
        NONE (int): No trigger set. `2`
    """

    ABOVE = 0
    BELOW = 1
    RISING = 2
    FALLING = 3
    RISING_OR_FALLING = 4
    ABOVE_LOWER = 5
    BELOW_LOWER = 6
    RISING_LOWER = 7
    FALLING_LOWER = 8
    INSIDE = ABOVE
    OUTSIDE = BELOW
    ENTER = RISING
    EXIT = FALLING
    ENTER_OR_EXIT = RISING_OR_FALLING
    POSITIVE_RUNT = 9
    NEGATIVE_RUNT = 10
    NONE = RISING


class TriggerState(IntEnum):
    """How each trigger condition is combined with the overall trigger logic.

    Attributes:
        DONT_CARE (int): The source condition has no effect on the logic. `0`
        TRUE (int): The source condition must be true. `1`
        FALSE (int): The source condition must be false. `2`
    """

    DONT_CARE = 0
    TRUE = 1
    FALSE = 2


class TriggerWithinPreTrigger(IntEnum):
    """Enable or disable the trigger during the pre-trigger period.

    Attributes:
        DISABLE (int): Uses triggering in the normal way. `0`
        ARM (int): Enables triggering anywhere within the pre-trigger samples. `1`
    """

    DISABLE = 0
    ARM = 1


class RatioMode(IntEnum):
    """Various methods of data reduction (down sampling).

    Attributes:
        NONE (int): No down sampling. `0`
        AGGREGATE (int): Reduces every block of n values to just two values: a minimum and a maximum. `1`
        DECIMATE (int): Reduces every block of n values to just the first value in the block,
            discarding all the other values. `2`
        AVERAGE (int): Reduces every block of n values to a single value representing the
            average (arithmetic mean) of all the values. `4`
        DISTRIBUTION (int): Not used. `8`
    """

    NONE = 0
    AGGREGATE = 1
    DECIMATE = 2
    AVERAGE = 4
    DISTRIBUTION = 8


class PulseWidthType(IntEnum):
    """The type of pulse-width trigger.

    Attributes:
        NONE (int): Do not use the pulse width qualifier. `0`
        LESS_THAN (int): Pulse width less than lower. `1`
        GREATER_THAN (int): Pulse width greater than lower. `2`
        IN_RANGE (int): Pulse width between lower and upper. `3`
        OUT_OF_RANGE (int): Pulse width not between lower and upper. `4`
    """

    NONE = 0
    LESS_THAN = 1
    GREATER_THAN = 2
    IN_RANGE = 3
    OUT_OF_RANGE = 4


class ChannelInfo(IntEnum):
    """Channel info enum.

    Attributes:
        RANGES (int): Supported channel ranges. `0`
    """

    RANGES = 0


@dataclass
class TriggerInfo:
    """The trigger timestamp information for the specified buffer segment.

    Attributes:
        segment_index (int): A zero-based index identifying the segment.
        trigger_index (int): The index of the trigger point measured in samples
            within the captured data, with the first sample being index 0.
        trigger_time (float): The trigger offset time, in seconds.
        timestamp_counter (int): The number of sample intervals between the trigger
            point of this segment and the previous segment. This allows you to
            determine the time interval between the trigger points of captures
            within a single rapid block run.
    """

    segment_index: int
    trigger_index: int
    trigger_time: float
    timestamp_counter: int


@final
class _TriggerInfo(Structure):
    _pack_ = 1
    _layout_ = "ms"
    _fields_ = (
        ("status", PICO_STATUS),
        ("segmentIndex", c_uint32),
        ("triggerIndex", c_uint32),
        ("triggerTime", c_int64),
        ("timeUnits", c_int16),
        ("reserved0", c_int16),
        ("timeStampCounter", c_uint64),
    )


@final
class Condition(Structure):
    """Trigger condition."""

    _pack_ = 1
    _layout_ = "ms"
    _fields_ = (
        ("source", c_uint32),
        ("condition", c_uint32),
    )

    def __init__(self, source: Channel | str | int, condition: TriggerState | str | int = "DONT_CARE") -> None:
        """Trigger condition.

        Args:
            source: The channel to use for the condition. Can be an enum member name (case insensitive) or value.
            condition: The trigger state of the `source`. Can be an enum member name (case insensitive) or value.
        """
        self.source: int = to_enum(source, Channel, to_upper=True)
        self.condition: int = to_enum(condition, TriggerState, to_upper=True)
        super().__init__(source=self.source, condition=self.condition)


@final
class Direction(Structure):
    """The direction in which the specified source signal must cross the threshold(s) to produce a trigger event."""

    _pack_ = 1
    _layout_ = "ms"
    _fields_ = (
        ("source", c_uint32),
        ("direction", c_uint32),
        ("mode", c_uint32),
    )

    def __init__(
        self,
        source: Channel | str | int,
        direction: ThresholdDirection | str | int = "rising",
        mode: ThresholdMode | str | int = "level",
    ) -> None:
        """The direction in which the specified source signal must cross the threshold(s) to produce a trigger event.

        Args:
            source: The channel to use for the trigger source. Can be an enum member name (case insensitive) or value.
            direction: The direction in which the signal must cross the threshold. Can be an enum member name
                (case insensitive) or value.
            mode: Whether to use a level trigger (a single threshold) or a window trigger
                (two thresholds defining a range).
        """
        self.source: int = to_enum(source, Channel, to_upper=True)
        self.direction: int = to_enum(direction, ThresholdDirection, to_upper=True)
        self.mode: int = to_enum(mode, ThresholdMode, to_upper=True)
        super().__init__(source=self.source, direction=self.direction, mode=self.mode)


@final
class TriggerChannelPropertiesV2(Structure):
    """The trigger thresholds for a given channel (version 2)."""

    _pack_ = 1
    _layout_ = "ms"
    _fields_ = (
        ("threshold_upper", c_int16),
        ("threshold_upper_hysteresis", c_uint16),
        ("threshold_lower", c_int16),
        ("threshold)_lower)_hysteresis", c_uint16),
        ("channel", c_uint32),
    )

    def __init__(
        self,
        threshold_upper: int,
        threshold_upper_hysteresis: int,
        threshold_lower: int,
        threshold_lower_hysteresis: int,
        channel: Channel | str | int,
    ) -> None:
        """The trigger thresholds for a given channel (version 2).

        Args:
            threshold_upper: The upper threshold at which the trigger must fire. This is scaled
                in 16-bit ADC counts at the currently selected range for that channel.
            threshold_upper_hysteresis: The hysteresis by which the trigger must exceed
                the upper threshold before it will fire. It is scaled in 16-bit counts.
            threshold_lower: The lower threshold at which the trigger must fire. This
                is scaled in 16-bit ADC counts at the currently selected range for that channel.
            threshold_lower_hysteresis: The hysteresis by which the trigger must exceed
                the lower threshold before it will fire. It is scaled in 16-bit counts.
            channel: The channel to which the properties apply. Can be an enum member name
                (case insensitive) or value.
        """
        self.threshold_upper: int = threshold_upper
        self.threshold_upper_hysteresis: int = threshold_upper_hysteresis
        self.threshold_lower: int = threshold_lower
        self.threshold_lower_hysteresis: int = threshold_lower_hysteresis
        self.channel: int = to_enum(channel, Channel, to_upper=True)
        super().__init__(
            threshold_upper=threshold_upper,
            threshold_upper_hysteresis=threshold_upper_hysteresis,
            threshold_lower=threshold_lower,
            threshold_lower_hysteresis=threshold_lower_hysteresis,
            channel=self.channel,
        )


@final
class DigitalChannelDirections(Structure):
    """The trigger direction for the specified digital channel."""

    _pack_ = 1
    _layout_ = "ms"
    _fields_ = (
        ("channel", c_uint32),
        ("direction", c_uint32),
    )

    def __init__(
        self,
        channel: int,
        direction: DigitalDirection | str | int,
    ) -> None:
        """The trigger direction for the specified digital channel.

        Args:
            channel: The digital channel number.
            direction: The direction in which the digital input must cross the threshold(s) to cause a trigger event.
                Can be an enum member name (case insensitive) or value.
        """
        self.channel: int = channel
        self.direction: int = to_enum(direction, DigitalDirection, to_upper=True)
        super().__init__(channel=channel, direction=self.direction)


def _configure(prefix: str, sdk: Any, errcheck: Callable[..., int]) -> None:  # noqa: ANN401
    """Configure the argtypes, restype and errcheck attributes of the SDK."""
    # These function must not use errcheck
    definitions: list[tuple[str, Any]]
    if prefix in {"ps5000a", "ps6000a"}:
        definitions = [("OpenUnit", (POINTER(c_int16), c_char_p, c_uint32))]
    else:
        definitions = [("OpenUnit", (POINTER(c_int16), c_char_p))]

    if prefix not in {"ps2000a", "ps6000a"}:
        definitions.append(("CurrentPowerSource", (c_int16,)))

    for fcn, argtypes in definitions:
        function = getattr(sdk, prefix + fcn)
        function.argtypes = argtypes
        function.restype = PICO_STATUS

    # These functions must use errcheck
    definitions = [
        ("ChangePowerSource", (c_int16, PICO_STATUS)),
        (
            "ChannelCombinationsStateless",
            (c_int16, POINTER(c_uint32), POINTER(c_uint32), c_uint32, c_uint32, c_int16),
        ),
        ("CheckForUpdate", (c_int16, c_void_p, c_void_p, POINTER(c_uint16))),
        ("CloseUnit", (c_int16,)),
        ("EnumerateUnits", (POINTER(c_int16), c_char_p, POINTER(c_int16))),
        ("FlashLed", (c_int16, c_int16)),
        ("GetAnalogueOffset", (c_int16, c_uint32, c_uint32, POINTER(c_float), POINTER(c_float))),
        ("GetChannelInformation", (c_int16, c_uint32, c_int32, POINTER(c_int32), POINTER(c_int32), c_int32)),
        ("GetDeviceResolution", (c_int16, POINTER(c_uint32))),
        ("GetMaxDownSampleRatio", (c_int16, c_uint32, POINTER(c_uint32), c_uint32, c_uint32)),
        ("GetMaxSegments", (c_int16, POINTER(c_uint32))),
        ("GetMinimumTimebaseStateless", (c_int16, c_uint32, POINTER(c_uint32), POINTER(c_double), c_uint32)),
        ("GetNoOfCaptures", (c_int16, POINTER(c_uint32))),
        ("GetNoOfProcessedCaptures", (c_int16, POINTER(c_uint32))),
        ("GetStreamingLatestValues", (c_int16, _StreamingReady, c_void_p)),
        ("GetTimebase", (c_int16, c_uint32, c_int32, POINTER(c_int32), POINTER(c_int32), c_uint32)),
        ("GetTimebase2", (c_int16, c_uint32, c_int32, POINTER(c_float), POINTER(c_int32), c_uint32)),
        ("GetTriggerInfoBulk", (c_int16, POINTER(_TriggerInfo), c_uint32, c_uint32)),
        ("GetTriggerTimeOffset", (c_int16, POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint32), c_uint32)),
        ("GetTriggerTimeOffset64", (c_int16, POINTER(c_int64), POINTER(c_uint32), c_uint32)),
        ("GetUnitInfo", (c_int16, c_char_p, c_int16, POINTER(c_int16), c_uint32)),
        ("GetValues", (c_int16, c_uint32, POINTER(c_uint32), c_uint32, c_uint32, c_uint32, POINTER(c_int16))),
        (
            "GetValuesAsync",
            (c_int16, c_uint32, c_uint32, c_uint32, c_uint32, c_uint32, _DataReady, c_void_p),
        ),
        (
            "GetValuesBulk",
            (c_int16, POINTER(c_uint32), c_uint32, c_uint32, c_uint32, c_uint32, POINTER(c_int16)),
        ),
        (
            "GetValuesOverlapped",
            (c_int16, c_uint32, POINTER(c_uint32), c_uint32, c_uint32, c_uint32, POINTER(c_int16)),
        ),
        (
            "GetValuesOverlappedBulk",
            (c_int16, c_uint32, POINTER(c_uint32), c_uint32, c_uint32, c_uint32, c_uint32, POINTER(c_int16)),
        ),
        (
            "GetValuesTriggerTimeOffsetBulk",
            (c_int16, POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint32), c_uint32, c_uint32),
        ),
        ("GetValuesTriggerTimeOffsetBulk64", (c_int16, POINTER(c_int64), POINTER(c_uint32), c_uint32, c_uint32)),
        ("IsLedFlashing", (c_int16, POINTER(c_int16))),
        ("IsReady", (c_int16, POINTER(c_int16))),
        ("IsTriggerOrPulseWidthQualifierEnabled", (c_int16, POINTER(c_int16), POINTER(c_int16))),
        ("MaximumValue", (c_int16, POINTER(c_int16))),
        ("MemorySegments", (c_int16, c_uint32, POINTER(c_int32))),
        ("MinimumValue", (c_int16, POINTER(c_int16))),
        (
            "NearestSampleIntervalStateless",
            (c_int16, c_uint32, c_double, c_uint32, c_uint16, POINTER(c_uint32), POINTER(c_double)),
        ),
        ("NoOfStreamingValues", (c_int16, POINTER(c_uint32))),
        ("PingUnit", (c_int16,)),
        ("QueryOutputEdgeDetect", (c_int16, POINTER(c_int16))),
        (
            "RunBlock",
            (c_int16, c_int32, c_int32, c_uint32, POINTER(c_int32), c_uint32, _BlockReady, c_void_p),
        ),
        (
            "RunStreaming",
            (c_int16, POINTER(c_uint32), c_uint32, c_uint32, c_uint32, c_int16, c_uint32, c_uint32, c_uint32),
        ),
        ("SetBandwidthFilter", (c_int16, c_uint32, c_uint32)),
        ("SetChannel", (c_int16, c_uint32, c_int16, c_uint32, c_uint32, c_float)),
        (
            "SetDataBuffer",
            (c_int16, c_uint32, ndpointer(dtype=c_int16, flags="C_CONTIGUOUS"), c_int32, c_uint32, c_uint32),
        ),
        ("SetDataBuffers", (c_int16, c_uint32, POINTER(c_int16), POINTER(c_int16), c_int32, c_uint32, c_uint32)),
        ("SetDeviceResolution", (c_int16, c_uint32)),
        ("SetDigitalPort", (c_int16, c_uint32, c_int16, c_int16)),
        ("SetEts", (c_int16, c_uint32, c_int16, c_int16, POINTER(c_int32))),
        ("SetEtsTimeBuffer", (c_int16, ndpointer(dtype=c_int64, ndim=1, flags="C_CONTIGUOUS"), c_int32)),
        ("SetEtsTimeBuffers", (c_int16, POINTER(c_uint32), POINTER(c_uint32), c_int32)),
        ("SetNoOfCaptures", (c_int16, c_uint32)),
        ("SetOutputEdgeDetect", (c_int16, c_int16)),
        ("SetPulseWidthDigitalPortProperties", (c_int16, POINTER(DigitalChannelDirections), c_int16)),
        (
            "SetPulseWidthQualifier",
            (c_int16, c_void_p, c_int16, c_uint32, c_uint32, c_uint32, c_uint32),
        ),
        ("SetPulseWidthQualifierConditions", (c_int16, POINTER(Condition), c_int16, c_uint32)),
        ("SetPulseWidthQualifierDirections", (c_int16, POINTER(Direction), c_int16)),
        ("SetPulseWidthQualifierProperties", (c_int16, c_uint32, c_uint32, c_uint32)),
        ("SetTriggerDigitalPortProperties", (c_int16, POINTER(DigitalChannelDirections), c_int16)),
        (
            "SetSigGenArbitrary",
            (
                c_int16,
                c_int32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                ndpointer(dtype=c_int16, ndim=1, flags="C_CONTIGUOUS"),
                c_int32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_int16,
            ),
        ),
        (
            "SetSigGenBuiltInV2",
            (
                c_int16,
                c_int32,
                c_uint32,
                c_uint32,
                c_double,
                c_double,
                c_double,
                c_double,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_int16,
            ),
        ),
        (
            "SetSigGenPropertiesArbitrary",
            (
                c_int16,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_int16,
            ),
        ),
        (
            "SetSigGenPropertiesBuiltIn",
            (
                c_int16,
                c_double,
                c_double,
                c_double,
                c_double,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_uint32,
                c_int16,
            ),
        ),
        ("SetSimpleTrigger", (c_int16, c_int16, c_uint32, c_int16, c_uint32, c_uint32, c_int16)),
        ("SetUnscaledDataBuffers", (c_int16, c_uint32, c_int8, c_int8, c_int32, c_uint32, c_uint32)),
        ("SetTriggerChannelConditions", (c_int16, c_void_p, c_int16)),
        ("SetTriggerChannelConditionsV2", (c_int16, POINTER(Condition), c_int16, c_int32)),
        ("SetTriggerChannelDirections", (c_int16, c_uint32, c_uint32, c_uint32, c_uint32, c_uint32, c_uint32)),
        ("SetTriggerChannelDirectionsV2", (c_int16, POINTER(Direction), c_uint16)),
        ("SetTriggerChannelPropertiesV2", (c_int16, POINTER(TriggerChannelPropertiesV2), c_int16, c_int16)),
        ("SetAutoTriggerMicroSeconds", (c_int16, c_uint64)),
        ("SetTriggerDelay", (c_int16, c_uint32)),
        (
            "SigGenArbitraryMinMaxValues",
            (c_int16, POINTER(c_int16), POINTER(c_int16), POINTER(c_uint32), POINTER(c_uint32)),
        ),
        ("SigGenFrequencyToPhase", (c_int16, c_double, c_uint32, c_uint32, POINTER(c_uint32))),
        ("SigGenSoftwareControl", (c_int16, c_int16)),
        ("Stop", (c_int16,)),
        ("TriggerWithinPreTriggerSamples", (c_int16, c_uint32)),
    ]

    for name, argtypes in definitions:
        fcn = prefix + name
        try:
            function = getattr(sdk, fcn)
        except AttributeError:

            def not_implemented(*_: int, f: str = fcn) -> Never:
                msg = f"{f!r} is not implemented in the Pico Technology SDK"
                raise NotImplementedError(msg)

            setattr(sdk, fcn, partial(not_implemented, f=fcn))
            continue

        function.argtypes = argtypes
        function.restype = PICO_STATUS
        function.errcheck = errcheck

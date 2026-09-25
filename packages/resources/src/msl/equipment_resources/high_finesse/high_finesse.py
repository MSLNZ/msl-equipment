"""Connect to a Wavelength Meter or Laser Spectrum Analyser from [HighFinesse](https://www.highfinesse.com/)."""

# cSpell: ignore Wavenumber Fizeau wavemeter
from __future__ import annotations

import os
from enum import IntEnum
from time import sleep
from typing import TYPE_CHECKING, NamedTuple

import numpy as np

from msl.equipment import Interface

from .wlm_data import Callback, WLMData

if TYPE_CHECKING:
    from ctypes import _CFunctionType  # pyright: ignore[reportPrivateUsage]

    from numpy.typing import NDArray

    from msl.equipment.schema import Equipment
    from msl.equipment.typing import PathLike

    from ..typing import HighFinesseCallback  # noqa: TID252


def high_finesse_callback(f: HighFinesseCallback) -> _CFunctionType:
    """Use as a decorator for a callback function when a new measurement is available.

    See [wavemeter_callback.py](https://github.com/MSLNZ/msl-equipment/blob/main/packages/resources/examples/high_finesse/wavemeter_callback.py)
    for an example usage.
    """
    return Callback(f)


class HighFinesse(Interface, manufacturer=r"High\s*Finesse"):
    """Connect to a Wavelength Meter or Laser Spectrum Analyser from [HighFinesse](https://www.highfinesse.com/)."""

    class WLMUnit(IntEnum):
        """HighFinesse measurement units.

        Attributes:
            Vacuum (int): 0 (nm)
            Air (int): 1 (nm)
            Frequency (int): 2 (THz)
            Wavenumber (int): 3 (1/cm)
            PhotonEnergy (int): 4 (eV)
        """

        Vacuum = 0
        Air = 1
        Frequency = 2
        Wavenumber = 3
        PhotonEnergy = 4

    class Range(IntEnum):
        """Wavelength ranges.

        Attributes:
            nm245_325 (int): `0`
            nm320_420 (int): `1`
            nm410_610 (int): `2`
            nm600_1190 (int): `3`
        """

        nm245_325 = 0
        nm320_420 = 1
        nm410_610 = 2
        nm600_1190 = 3

    class RangeModel(IntEnum):
        """Measurement range model constants.

        Attributes:
            Wavelength (int): `65533`
            Order (int): `65534`
            Old (int): `65535`
        """

        Wavelength = 65533
        Order = 65534
        Old = 65535

    def __init__(self, equipment: Equipment) -> None:
        r"""Connect to a Wavelength Meter or Laser Spectrum Analyser from [HighFinesse](https://www.highfinesse.com/).

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r""High\s*Finesse"
        ```

        Args:
            equipment: An [Equipment][] instance.
        """
        super().__init__(equipment)

        assert equipment.connection is not None  # noqa: S101
        path = equipment.connection.address[5:]

        # supports loading either the 32-bit or 64-bit library in 64-bit Python
        try:
            self._wlm: WLMData = WLMData(host=None, path=path)  # assume 64-bit library
        except OSError as e:
            if e.errno is None:  # File not found
                raise
            self._wlm = WLMData(host="127.0.0.1", path=path)  # assume 32-bit library

    @property
    def analysis_mode_state(self) -> bool:
        """Get/set whether the Laser Spectrum Analyser's analysis mode state is enabled or disabled."""
        return self._wlm.get_analysis_mode()

    @analysis_mode_state.setter
    def analysis_mode_state(self, mode: bool) -> None:
        self._wlm.set_analysis_mode(mode)

    @property
    def auto_exposure_state(self) -> bool:
        """Get/set whether the auto-exposure state is enabled or disabled."""
        return self._wlm.get_exposure_mode()

    @auto_exposure_state.setter
    def auto_exposure_state(self, mode: bool) -> None:
        self._wlm.set_exposure_mode(mode)

    def convert_unit(self, value: float, to: WLMUnit | int, frm: WLMUnit | int = WLMUnit.Vacuum) -> float:
        """Convert a value into a representation of another unit.

        Args:
            value: The value to convert. Must be &ge;0.
            to: The unit to convert `value` to.
            frm: The unit that `value` is currently in.

        Returns:
            The `value` in the converted unit.
        """
        # must convert IntEnum to int when loading the 32-bit library in 64-bit Python
        return self._wlm.convert_unit(value=value, frm=int(frm), to=int(to))

    def disconnect(self) -> None:  # pyright: ignore[reportImplicitOverride]
        """Clean up the library resources."""
        if hasattr(self, "_wlm"):
            _ = self._wlm.shutdown_server32()
        return super().disconnect()

    def get_exposure_time(self, index: int = 1, channel: int = 1) -> int:
        """Get the exposure time (in ms).

        Args:
            index: The CCD array index for devices with more than one CCD array.
                Can be 1 or 2. For devices with only one CCD array set the value to be 1.
            channel: The signal channel for devices with a multichannel switcher.
                Should be set to 1 for devices that do not have this option.

        Returns:
            The exposure time (in ms).
        """
        return self._wlm.get_exposure_num(channel=channel, index=index)

    def interferometer_data(self, index: int, channel: int = 1) -> NDArray[np.uint16]:
        """Get the interferometer pattern data.

        Args:
            index: The index of the data type to receive.

                * 0 - Fizeau interferometers or diffraction grating
                * 1 - Additional long interferometer or grating analysing versions (spectrum analysis)
                * 2 - Fizeau interferometers that support double pulses
                * 3 - Additional interferometer for second pulse

            channel: Identifies the switcher channel number. Devices without a switcher must use 1.

        Returns:
            The interferometer pattern data. If all values in the array are zero, try calling this method again.
        """
        return np.array(self._wlm.interferometer_data(index=index, channel=channel), dtype=np.uint16)

    def operation(self, mode: int) -> int:
        """Set the program measurement action mode and enables loading and recording files.

        Args:
            mode: Controls how a measurement or file accessing activity will be started or stopped.
                For example, `mode=0` (*cCtrlStopAll*) stops all measurement activities, as well
                as adjustments, recordings and replaying. See the manual for more details.
        """
        return self._wlm.operation(mode)

    def run_software(self, path: PathLike, *, wait: bool = True) -> None:
        """Run the HighFinesse application software.

        It is okay to call this method if the software is already running.

        !!! warning
            The HighFinesse application software must be running for the SDK functions to work properly.

        Args:
            path: The path to the HighFinesse executable for the application software,
                e.g., `"C:/Program Files (x86)/HighFinesse/Wavelength Meter WS5 <SERIAL#>/wlm_ws5.exe"`
            wait: Whether to wait for the software to perform its initialisation before returning
                to the calling program. The device may still not be ready to get/set parameters
                when this method returns.
        """
        result = self._wlm.control_wlm(action=1, path=os.fsencode(path))  # cCtrlWLMShow=1
        if result == 0:
            msg = f"Cannot run '{os.fsdecode(path)}'"
            raise OSError(msg)

        if wait:
            while True:
                if self._wlm.get_wlm_count() > 0:
                    return
                sleep(1)

    def set_callback(self, function: HighFinesseCallback | None, priority: int = 2) -> None:
        """Set a callback function.

        Args:
            function: A callback function to register when a new measurement is available.
                Set to `None` to unregister the callback.
            priority: Callback thread priority. Set to `0` to use *standard* priority.
        """
        if self._wlm.host is not None:
            if function is None:
                return

            msg = "Using a callback function is only supported when a 64-bit library of the SDK is used"
            raise RuntimeError(msg)

        if function is None:
            r = self._wlm.instantiate(rfc=1, mode=1, p1=None, p2=0)
        else:
            r = self._wlm.instantiate(rfc=1, mode=4, p1=function, p2=priority)

        if r == 0:
            msg = "Could not set callback function"
            raise RuntimeError(msg)

    def set_exposure_time(self, ms: int, index: int = 1, channel: int = 1) -> None:
        """Set the exposure time (in ms).

        Args:
            ms: The exposure time, in ms.
            index: The CCD array index for devices with more than one CCD array.
                Can be 1 or 2. For devices with only one CCD array set the
                value to be 1.
            channel: The signal channel for devices with a multichannel switcher.
                Should be set to 1 for devices that do not have this option.
        """
        self._wlm.set_exposure_time(ms=ms, channel=channel, index=index)

    def start_measurement(self) -> None:
        """Start measurement."""
        _ = self.operation(2)  # cCtrlStartMeasurement

    def stop_measurement(self) -> None:
        """Stop measurement."""
        _ = self.operation(0)  # cCtrlStopAll

    def temperature(self) -> float:
        """Returns the temperature inside the device, in Celsius."""
        return self._wlm.get_temperature()

    def version_info(self) -> WLMVersionInfo:
        """Get the version information about the device."""
        return WLMVersionInfo(*self._wlm.get_wlm_version())

    def wavelength(self, number: int = 0) -> float:
        """Get the vacuum wavelength (in nm).

        Args:
            number: The signal number (1 to 8) if the device has a multichannel switcher or
                contains the double-pulse option. For devices without these options set to 0.

        Returns:
            The latest vacuum wavelength (in nm) that was measured.
        """
        return self._wlm.get_wavelength_num(number)


class WLMVersionInfo(NamedTuple):
    """Version information about the wavelength meter or laser spectrum analyser.

    Attributes:
        device_type (int): Device type.
        serial_number (int): Serial number.
        software_revision (int): Software revision number.
        software_compilation (int): Software compilation number.
    """

    device_type: int
    serial_number: int
    software_revision: int
    software_compilation: int

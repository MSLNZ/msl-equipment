"""Communicate with a SuperK laser from NKT Photonics."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, NamedTuple

from msl.equipment.interfaces.message_based import MSLConnectionError

from .nkt import NKT

if TYPE_CHECKING:
    from typing import Literal

    from msl.equipment.schema import Equipment

    from .nkt import Module


class _Key(IntEnum):
    temperature = 0
    emission = 1
    operating_mode = 2
    interlock = 3
    pulse_picker_ratio = 4
    watchdog_interval = 5
    output_level = 6
    power_level = 7
    current_level = 8
    nim_delay = 9
    system_type = 10
    user_text = 11
    user_setup = 12
    max_pulse_picker_ratio = 13
    display_text = 14
    panel_lock = 15
    error_flash = 16


class _S(NamedTuple):
    register: int  # register address
    dtype: Literal["i8", "u8", "h8", "i16", "u16", "h16", "i32", "u32", "h32"] | None


# SDK\Register Files\60.txt
_0x60 = {
    # Readings
    _Key.temperature: _S(0x11, "i16"),
    _Key.system_type: _S(0x6B, "u8"),
    # Controls
    _Key.emission: _S(0x30, "u8"),
    _Key.operating_mode: _S(0x31, "u16"),
    _Key.interlock: _S(0x32, "u16"),
    _Key.pulse_picker_ratio: _S(0x34, "u16"),
    _Key.watchdog_interval: _S(0x36, "u8"),
    _Key.power_level: _S(0x37, "u16"),
    _Key.current_level: _S(0x38, "u16"),
    _Key.nim_delay: _S(0x39, "u16"),
    _Key.user_text: _S(0x6C, None),
    # SuperK Front panel 2011 (SDK\Register Files\61.txt)
    # Readings
    _Key.display_text: _S(0x72, None),
    # Controls
    _Key.panel_lock: _S(0x3D, "u8"),
    _Key.error_flash: _S(0x8D, "u8"),
}

# SDK\Register Files\88.txt
_0x88 = {
    # Readings
    _Key.temperature: _S(0x11, "i16"),
    _Key.max_pulse_picker_ratio: _S(0x3D, "u16"),
    # Controls
    _Key.emission: _S(0x30, "u8"),
    _Key.operating_mode: _S(0x31, "u8"),
    _Key.interlock: _S(0x32, "u16"),
    _Key.pulse_picker_ratio: _S(0x34, "u16"),
    _Key.watchdog_interval: _S(0x36, "u8"),
    _Key.output_level: _S(0x37, "u16"),
    _Key.nim_delay: _S(0x39, "u16"),
    _Key.user_setup: _S(0x3B, "u16"),
    _Key.user_text: _S(0x8D, None),
}

_modules = {
    0x60: _0x60,  # SuperK EXTREME
    0x88: _0x88,  # SuperK FIANIUM
}


@dataclass
class UserSetup:
    """SuperK user setup.

    Attributes:
        nim_output (bool): Whether the laser's pulse output is a NIM-style output
            (negative current) or a positive pulse output.
    """

    nim_output: bool


class SuperK(NKT, manufacturer=r"^NKT", model=r"SuperK"):
    """Communicate with a SuperK laser from NKT Photonics."""

    class OperatingMode(IntEnum):
        """The operating mode of a SuperK laser.

        Attributes:
            INTERNAL_POWER (int): SuperK FIANIUM, `0`
            CONSTANT_CURRENT (int): SuperK EXTREME, `0`
            CONSTANT_POWER (int): SuperK EXTREME, `1`
            MODULATED_CURRENT (int): SuperK EXTREME, `2`
            MODULATED_POWER (int): SuperK EXTREME, `3`
            EXTERNAL_FEEDBACK (int): SuperK EXTREME and FIANIUM, `4`
        """

        INTERNAL_POWER = 0
        CONSTANT_CURRENT = 0
        CONSTANT_POWER = 1
        MODULATED_CURRENT = 2
        MODULATED_POWER = 3
        EXTERNAL_FEEDBACK = 4

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with a SuperK laser from NKT Photonics.

        *SuperK EXTREME* and *SuperK FIANIUM* are supported.

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"^NKT"
        model=r"SuperK"
        ```

        Args:
            equipment: An [Equipment][] instance.

        A [Connection][msl.equipment.schema.Connection] instance supports the following _properties_
        for the `SuperK` class plus all the _properties_ of the [NKT][msl.equipment_resources.nkt.NKT] class.

        Attributes: Connection Properties:
            ensure_interlock_ok (bool): Whether to make sure the interlock status is okay after connecting.
                _Default: `True`_
            scan_timeout (float): The maximum number of seconds to wait for a reply when scanning for the
                SuperK mainboard module. _Default: `5.0`_
        """
        super().__init__(equipment)
        assert equipment.connection is not None  # noqa: S101

        superk_address = 15
        t = equipment.connection.properties.get("scan_timeout", 5.0)
        self._module: Module = self.scan_modules(start=superk_address, stop=superk_address, timeout=t)[0]
        self._is_fianium: bool = self._module.type == 0x88  # noqa: PLR2004

        settings = _modules.get(self._module.type)
        if settings is None:
            msg = f"SuperK module is not supported: {self._module}"
            raise MSLConnectionError(self, msg)

        self._settings: dict[_Key, _S] = settings

        if equipment.connection.properties.get("ensure_interlock_ok", True):
            self.ensure_interlock_ok()

    def _mode_to_output_key(self, action: str) -> _Key:
        if self._is_fianium:
            return _Key.output_level

        mode = self.operating_mode
        if mode == self.OperatingMode.CONSTANT_POWER:
            return _Key.power_level

        if mode in {self.OperatingMode.CONSTANT_CURRENT, self.OperatingMode.EXTERNAL_FEEDBACK}:
            return _Key.current_level

        msg = f"Cannot {action} the output level when the operating mode is {mode!r}"
        raise ValueError(msg)

    def ensure_interlock_ok(self) -> None:
        """Make sure that the interlock is okay.

        Raises [MSLConnectionError][msl.equipment.interfaces.message_based.MSLConnectionError]
        if it is not okay and it cannot be reset.
        """
        register, dtype = self._settings[_Key.interlock]
        assert dtype is not None  # noqa: S101

        module = self._module.address
        status = self.read_register(module, register, dtype)
        if status & 0x0002:
            return

        if status & 0x0001:  # waiting for an interlock reset
            self.write_register(module, register, value=1, dtype=dtype)
            status = self.read_register(module, register, dtype)
            if status & 0x0002:
                return

        msg = f"Interlock not okay [status code={status}]"
        if status & 0x0100:
            msg += ", is the key in the off position?"
        raise MSLConnectionError(self, msg)

    @property
    def emission(self) -> bool:
        """Turn the emission on (`True`) or off (`False`)."""
        register, dtype = self._settings[_Key.emission]
        return bool(self.read_register(self._module.address, register, dtype))

    @emission.setter
    def emission(self, state: bool) -> None:
        register, dtype = self._settings[_Key.emission]
        value = 3 if state else 0
        self.write_register(self._module.address, register, value=value, dtype=dtype)

    @property
    def is_fianium(self) -> bool:
        """Whether the SuperK laser system is FIANIUM."""
        return self._is_fianium

    @property
    def lock_front_panel(self) -> bool:
        """Lock the front panel so that the current or power level cannot be changed.

        Not all SuperK lasers support front-panel locking. If the laser does not support
        this feature, setting this property does nothing.
        """
        try:
            register, dtype = self._settings[_Key.panel_lock]
        except KeyError:
            return False
        else:
            # front-panel address is 1
            return bool(self.read_register(1, register, dtype=dtype))

    @lock_front_panel.setter
    def lock_front_panel(self, state: bool) -> None:
        try:
            register, dtype = self._settings[_Key.panel_lock]
        except KeyError:
            pass
        else:
            # front-panel address is 1
            self.write_register(1, register, value=int(state), dtype=dtype)

    @property
    def nim_delay(self) -> int:
        """Get/set the NIM trigger delay (in picoseconds).

        The range is 0 - 9200 ps with an average step size of approximately 15 ps.
        """
        register, dtype = self._settings[_Key.nim_delay]
        assert dtype is not None  # noqa: S101
        return self.read_register(self._module.address, register, dtype)

    @nim_delay.setter
    def nim_delay(self, delay: int) -> None:
        register, dtype = self._settings[_Key.nim_delay]
        self.write_register(self._module.address, register, value=delay, dtype=dtype)

    @property
    def operating_mode(self) -> OperatingMode:
        """Get/set the operating mode."""
        register, dtype = self._settings[_Key.operating_mode]
        assert dtype is not None  # noqa: S101
        mode = self.read_register(self._module.address, register, dtype)
        if mode == 0:
            return self.OperatingMode.INTERNAL_POWER if self._is_fianium else self.OperatingMode.CONSTANT_CURRENT
        return self.OperatingMode(mode)

    @operating_mode.setter
    def operating_mode(self, mode: OperatingMode) -> None:
        register, dtype = self._settings[_Key.operating_mode]
        self.write_register(self._module.address, register, value=mode, dtype=dtype)

    @property
    def output(self) -> float:
        """Get/set the output level (as a percentage).

        The operating mode that the laser is currently in automatically handles whether
        the output level is for internal power/current or external feedback.
        """
        key = self._mode_to_output_key("get")
        register, dtype = self._settings[key]
        assert dtype is not None  # noqa: S101
        return round(self.read_register(self._module.address, register, dtype) * 0.1, 1)

    @output.setter
    def output(self, level: float) -> None:
        if level < 0 or level > 100:  # noqa: PLR2004
            msg = f"Invalid output level of {level}. Must be in the range [0, 100]."
            raise ValueError(msg)

        key = self._mode_to_output_key("set")
        register, dtype = self._settings[key]
        value = round(level * 10)
        self.write_register(self._module.address, register, value=value, dtype=dtype)

    @property
    def pulse_picker_ratio(self) -> int:
        """Get/set the pulse-picker ratio."""
        register, dtype = self._settings[_Key.pulse_picker_ratio]
        assert dtype is not None  # noqa: S101
        try:
            return self.read_register(self._module.address, register, dtype)
        except struct.error:
            # From the SDK manual for the SuperK EXTREME:
            #   When reading the pulse picker value, an 8-bit unsigned integer is returned if
            #   the ratio is lower than 256, otherwise a 16-bit unsigned integer is returned.
            #   This is for historical reasons.
            return self.read_register(self._module.address, register, "u8")

    @pulse_picker_ratio.setter
    def pulse_picker_ratio(self, ratio: int) -> None:
        register, dtype = self._settings[_Key.pulse_picker_ratio]
        self.write_register(self._module.address, register, value=ratio, dtype=dtype)

    @property
    def status(self) -> int:
        """Get the mainboard status bytes."""
        return self.read_register(self._module.address, 0x66, "u16")

    @property
    def temperature(self) -> float:
        """Get the temperature of the laser."""
        register, dtype = self._settings[_Key.temperature]
        assert dtype is not None  # noqa: S101
        return round(self.read_register(self._module.address, register, dtype) * 0.1, 1)

    @property
    def user_setup(self) -> UserSetup:
        """Get/set the laser's user setup.

        Only valid for the SuperK FIANIUM.
        """
        if not self._is_fianium:
            msg = "Can only get the user setup for a SuperK FIANIUM laser"
            raise ValueError(msg)

        register, dtype = self._settings[_Key.user_setup]
        assert dtype is not None  # noqa: S101
        setup = self.read_register(self._module.address, register, dtype)
        return UserSetup(
            nim_output=not bool(setup & 1),
        )

    @user_setup.setter
    def user_setup(self, setup: UserSetup) -> None:
        if not self._is_fianium:
            msg = "Can only set the user setup for a SuperK FIANIUM laser"
            raise ValueError(msg)

        register, dtype = self._settings[_Key.user_setup]
        assert dtype is not None  # noqa: S101

        value = 0 if setup.nim_output else 1
        # as SuperK systems support more user-setup parameters use a bitwise or "|=" to build the value
        self.write_register(self._module.address, register, value=value, dtype=dtype)

    @property
    def user_text(self) -> str:
        """Get/set the user text.

        The text to read/write from/to the laser's firmware. Only ASCII characters are allowed.
        The maximum number of characters is 20 for SuperK EXTREME (module type 60h) and 240
        characters for SuperK FIANIUM (module type 0088h). SuperK EXTREME will also display
        the text on the front panel.
        """
        register, _ = self._settings[_Key.user_text]
        return self.read_register(self._module.address, register).rstrip(b"\x00").decode()

    @user_text.setter
    def user_text(self, text: str) -> None:
        # SuperK FIANIUM does not like getting an empty string
        if (not text) and self._is_fianium:
            text = " "

        register, _ = self._settings[_Key.user_text]
        self.write_register(self._module.address, register, value=text.encode("ascii"))

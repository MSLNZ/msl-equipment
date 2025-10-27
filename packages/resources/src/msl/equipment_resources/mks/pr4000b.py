"""Flow and Pressure controller, PR4000B, from [MKS](https://www.mks.com/) Instruments."""

# cSpell: ignore vvrrsssss ubar mbar MLIMIT MBAND SCCM SCFH SCFM
from __future__ import annotations

import re
from enum import IntEnum
from typing import TYPE_CHECKING

from msl.equipment.enumerations import DataBits
from msl.equipment.interfaces import MSLConnectionError, Serial
from msl.equipment.utils import to_enum

if TYPE_CHECKING:
    from typing import Literal

    from msl.equipment.schema import Equipment


MAX_RANGE = 10
MAX_POINT = 10
MAX_SIZE = 10
MAX_OFFSET = 250

ERROR_CODES = {
    "#E010": "Syntax Error",
    "#E020": "Failed to execute command",
    "#E001": "Communication Error",
    "#E002": "ADC Overflow or Underflow",
    "#E003": "Range Error, Setpoint < 0 or out of range",
    "#W001": "Offset > 250 mV",
}


class LimitMode(IntEnum):
    """Limit mode type.

    Attributes:
        SLEEP (int): 0
        LIMIT (int): 1
        BAND (int): 2
        MLIMIT (int): 3
        MBAND (int): 4
    """

    SLEEP = 0
    LIMIT = 1
    BAND = 2
    MLIMIT = 3
    MBAND = 4


class SignalMode(IntEnum):
    """Signal mode type.

    Determines the source of the setpoint which shall be applied to the respective channel.

    Attributes:
        METER (int): 0
        OFF (int): 1
        INDEPENDENT (int): 2
        EXTERNAL (int): 3
        SLAVE (int): 4
        RTD (int): 5
    """

    METER = 0
    OFF = 1
    INDEPENDENT = 2
    EXTERNAL = 3
    SLAVE = 4
    RTD = 5


class Tag(IntEnum):
    """Display tag types.

    Attributes:
        SP (int): 0
        VA (int): 1
        CH (int): 2
        FL (int): 3
        PR (int): 4
        EX (int): 5
    """

    SP = 0
    VA = 1
    CH = 2
    FL = 3
    PR = 4
    EX = 5


UNIT = {
    0: "ubar",
    1: "mbar",
    2: "bar",
    3: "mTorr",
    4: "Torr",
    5: "kTorr",
    6: "Pa",
    7: "kPa",
    8: "mH2O",
    9: "cH2O",
    10: "PSI",
    11: "N/qm",
    12: "SCCM",
    13: "SLM",
    14: "SCM",
    15: "SCFH",
    16: "SCFM",
    17: "mA",
    18: "V",
    19: "%",
    20: "C",
}
"""Mapping from an index value to a unit name."""


class PR4000B(Serial, manufacturer=r"^MKS", model=r"PR4000B", flags=re.IGNORECASE):
    """Flow and Pressure controller, PR4000B, from [MKS](https://www.mks.com/) Instruments."""

    def __init__(self, equipment: Equipment) -> None:
        """Flow and Pressure controller, PR4000B, from [MKS](https://www.mks.com/) Instruments.

        The default settings for the RS232 connection are:

        * Baud rate: 9600
        * Parity: ODD
        * Data bits: 7
        * Stop bits: 1
        * Flow control: None

        The baud rate and parity can be changed on the controller. The data bits,
        stop bits, and flow control cannot be changed. A null modem (cross over)
        cable is required when using a USB to RS232 converter. RS485 support is
        not implemented.

        Args:
            equipment: An [Equipment][] instance..
        """
        assert equipment.connection is not None  # noqa: S101
        equipment.connection.properties.setdefault("data_bits", DataBits.SEVEN)
        super().__init__(equipment)
        self.read_termination: bytes = b"\r"
        self.write_termination: bytes = b"\r"

    def _check(self, command: str) -> str:
        """Send a command then check the reply for an error.

        Args:
            command: The command to query.

        Returns:
            The reply if the there was no error, otherwise raises an exception.
        """
        reply = self.query(command)
        if reply.startswith("#"):
            msg = ERROR_CODES.get(reply, "Undefined error code")
            raise MSLConnectionError(self, f"{reply}: {msg}")
        return reply

    def _check_channel(self, channel: int) -> None:
        if channel not in {1, 2}:
            msg = f"Invalid channel {channel}"
            raise ValueError(msg)

    def auto_zero(self, channel: Literal[1, 2]) -> int:
        """Auto zero a channel.

        Args:
            channel: The channel number.

        Returns:
            The offset.
        """
        self._check_channel(channel)
        return int(self.query(f"AZ{channel}"))

    def default(self, mode: Literal["pressure", "p", "flow", "f"]) -> None:
        """Reset to the default configuration.

        Args:
            mode: The mode to reset.
        """
        upper = mode.upper()
        if upper not in {"P", "F", "PRESSURE", "FLOW"}:
            msg = f"Invalid default mode {mode!r}, must one of: pressure, flow, p or f"
            raise ValueError(msg)

        _ = self._check(f"DF,{upper[0]}")

    def display_enable(self, display: Literal[1, 2, 3, 4], *, enable: bool) -> None:
        """Turn a display on or off.

        Args:
            display: The display number.
            enable: Whether to turn the display on (`True`) or off (`False`).
        """
        if display not in {1, 2, 3, 4}:
            msg = f"Invalid display number {display}, must be 1, 2, 3 or 4"
            raise ValueError(msg)

        state = "ON" if enable else "OFF"
        _ = self._check(f"DP{display},{state}")

    def display_setup(
        self, display: Literal[1, 2, 3, 4], line: Literal[1, 2], channel: Literal[1, 2], tag: int | str | Tag
    ) -> None:
        """Configure a display.

        Args:
            display: The display number.
            line: The line number.
            channel: The channel number.
            tag: The tag to use. Can be a [Tag][msl.equipment_resources.mks.pr4000b.Tag] member name or value.
                For example, `Tag.PR`, `4`, or `"PR"` are equivalent.
        """
        if display not in {1, 2, 3, 4}:
            msg = f"Invalid display number {display}, must be 1, 2, 3 or 4"
            raise ValueError(msg)

        if line not in {1, 2}:
            msg = f"Invalid line number {line}, must be 1 or 2"
            raise ValueError(msg)

        self._check_channel(channel)
        tag = to_enum(tag, Tag, to_upper=True)
        _ = self._check(f"DP{display},{line},{tag},{channel}")

    def display_4(self, *, enable: bool) -> None:
        """Whether to enable or disable display 4.

        Args:
            enable: Whether to enable or disable display 4.
        """
        state = "ON" if enable else "OFF"
        _ = self._check(f"DP4,{state}")

    def external_input(self, channel: Literal[1, 2]) -> float:
        """Return the external input of a channel.

        Args:
            channel: The channel number.

        Returns:
            The external input.
        """
        self._check_channel(channel)
        return float(self.query(f"EX{channel}"))

    def get_access_channel(self, channel: Literal[1, 2]) -> tuple[float, bool]:
        """Get the setpoint and the state of the valve of a channel.

        Args:
            channel: The channel number.

        Returns:
            The setpoint value and whether the valve is on (`True`) or off (`False`).
        """
        self._check_channel(channel)
        a, b = self.query(f"?AC{channel}").rstrip().split(",")
        return float(a), b == "ON"

    def get_actual_value(self, channel: Literal[1, 2]) -> float:
        """Get the actual value of a channel.

        Args:
            channel: The channel number.

        Returns:
            The value.
        """
        self._check_channel(channel)
        return float(self.query(f"AV{channel}"))

    def get_address(self) -> int:
        """Get the address.

        Returns:
            The address.
        """
        return int(self.query("?AD"))

    def get_dead_band(self, channel: Literal[1, 2]) -> float:
        """Get the dead band of a channel.

        Args:
            channel: The channel number.

        Returns:
            The dead band.
        """
        self._check_channel(channel)
        return float(self.query(f"?DB{channel}"))

    def get_dialog(self) -> int:
        """Get the current dialog index that is displayed.

        Returns:
            The dialog index.
        """
        return int(self.query("?DG"))

    def get_display_text(self) -> str:
        """Get the display text.

        Returns:
            The display text.
        """
        return self.query("?DT").rstrip()

    def get_external_input_range(self, channel: Literal[1, 2]) -> int:
        """Get the external input range of a channel.

        Args:
            channel: The channel number.

        Returns:
            The external input range.
        """
        self._check_channel(channel)
        return int(self.query(f"?EI{channel}"))

    def get_external_output_range(self, channel: Literal[1, 2]) -> int:
        """Get the external output range of a channel.

        Args:
            channel: The channel number.

        Returns:
            The external output range.
        """
        self._check_channel(channel)
        return int(self.query(f"?EO{channel}"))

    def get_formula_relay(self, channel: Literal[1, 2]) -> str:
        """Get the relay formula of a channel.

        Args:
            channel: The channel number.

        Returns:
            The formula.
        """
        self._check_channel(channel)
        return self.query(f"?FR{channel}").strip()

    def get_formula_temporary(self, channel: Literal[1, 2]) -> str:
        """Get the temporary formula of a channel.

        Args:
            channel: The channel number.

        Returns:
            The formula.
        """
        self._check_channel(channel)
        return self.query(f"?FT{channel}").strip()

    def get_gain(self, channel: Literal[1, 2]) -> float:
        """Get the gain of a channel.

        Args:
            channel: The channel number.

        Returns:
            The gain.
        """
        self._check_channel(channel)
        return float(self.query(f"?GN{channel}"))

    def get_input_range(self, channel: Literal[1, 2]) -> int:
        """Get the input range of a channel.

        Args:
            channel: The channel number.

        Returns:
            The input range.
        """
        self._check_channel(channel)
        return int(self.query(f"?IN{channel}"))

    def get_interface_mode(self) -> int:
        """Get the interface mode.

        Returns:
            The interface mode.
        """
        return int(self.query("?IM"))

    def get_limit_mode(self, channel: Literal[1, 2]) -> LimitMode:
        """Get the limit mode of a channel.

        Args:
            channel: The channel number.

        Returns:
            The limit mode.
        """
        self._check_channel(channel)
        mode = int(self.query(f"?LM{channel}"))
        return LimitMode(mode)

    def get_linearization_point(self, channel: Literal[1, 2], point: int) -> tuple[float, float]:
        """Get the point in the linearization table of a channel.

        Args:
            channel: The channel number.
            point: The point in the table [0, 10].

        Returns:
            The `(x, y)` point.
        """
        self._check_channel(channel)
        if point < 0 or point > MAX_POINT:
            msg = f"Invalid point {point}, must be between [0, 10]"
            raise ValueError(msg)
        a, b = self.query(f"?LN{channel},{point}").split(",")
        return float(a), float(b)

    def get_linearization_size(self, channel: Literal[1, 2]) -> int:
        """Get the size of the linearization table of a channel.

        Args:
            channel: The channel number.

        Returns:
            The size of the table.
        """
        self._check_channel(channel)
        return int(self.query(f"?LS{channel}"))

    def get_lower_limit(self, channel: Literal[1, 2]) -> float:
        """Get the lower limit of a channel.

        Args:
            channel: The channel number.

        Returns:
            The lower limit.
        """
        self._check_channel(channel)
        return float(self.query(f"?LL{channel}"))

    def get_offset(self, channel: Literal[1, 2]) -> int:
        """Get the offset of a channel.

        Args:
            channel: The channel number.

        Returns:
            The offset.
        """
        self._check_channel(channel)
        return int(self.query(f"?OF{channel}"))

    def get_output_range(self, channel: Literal[1, 2]) -> int:
        """Get the output range of a channel.

        Args:
            channel: The channel number.

        Returns:
            The output range.
        """
        self._check_channel(channel)
        return int(self.query(f"?OT{channel}"))

    def get_range(self, channel: Literal[1, 2]) -> tuple[float, int, str]:
        """Get the range and unit of a channel.

        Args:
            channel: The channel number.

        Returns:
            The range, unit index and unit name.
        """
        self._check_channel(channel)
        a, b = self.query(f"?RG{channel}").split(",")
        unit = int(b)
        return float(a), unit, UNIT[unit]

    def get_relays(self, channel: Literal[1, 2]) -> bool:
        """Get the relay state of a channel.

        Args:
            channel: The channel number.

        Returns:
            Whether the relay is enabled or disabled.
        """
        self._check_channel(channel)
        return self.query(f"?RL{channel}").rstrip() == "ON"

    def get_remote_mode(self) -> bool:
        """Get the remote operation mode.

        Returns:
            Whether the remote operation mode is enabled (`True`) or disabled (`False`).
        """
        return self.query("?RT").rstrip() == "ON"

    def get_resolution(self) -> bool:
        """Get whether 16-bit resolution is enabled.

        Returns:
            Whether 16-bit resolution is enabled (`True`) or disabled (`False`).
        """
        return self.query("?RS").rstrip() == "ON"

    def get_rtd_offset(self, channel: Literal[1, 2]) -> int:
        """Get the RTD offset of a channel.

        Args:
            channel: The channel number.

        Returns:
            The offset.
        """
        self._check_channel(channel)
        return int(self.query(f"?RO{channel}"))

    def get_scale(self, channel: Literal[1, 2]) -> float:
        """Get the scale of a channel.

        Args:
            channel: The channel number.

        Returns:
            The scale.
        """
        return float(self.query(f"?SC{channel}"))

    def get_setpoint(self, channel: Literal[1, 2]) -> float:
        """Get the setpoint of a channel.

        Args:
            channel: The channel number.

        Returns:
            The setpoint.
        """
        self._check_channel(channel)
        return float(self.query(f"?SP{channel}"))

    def get_signal_mode(self, channel: Literal[1, 2]) -> SignalMode:
        """Get the signal mode of a channel.

        Args:
            channel: The channel number.

        Returns:
            The signal mode.
        """
        self._check_channel(channel)
        mode = int(self.query(f"?SM{channel}"))
        return SignalMode(mode)

    def get_upper_limit(self, channel: Literal[1, 2]) -> float:
        """Get the upper limit of a channel.

        Args:
            channel: The channel number.

        Returns:
            The upper limit.
        """
        self._check_channel(channel)
        return float(self.query(f"?UL{channel}"))

    def get_valve(self, channel: Literal[1, 2]) -> bool:
        """Get the state of the valve of a channel.

        Args:
            channel: The channel number.

        Returns:
            Whether the valve is enabled (`True`) or disabled (`False`).
        """
        self._check_channel(channel)
        return self.query(f"?VL{channel}").rstrip() == "ON"

    def identity(self) -> str:
        """Returns the identity.

        Returns:
            The identity. For example, `PR42vvrrsssss`, where `vv` is the version,
                `rr` is the release and `sssss` is the serial number.
        """
        return self.query("?ID").rstrip()

    def lock(self) -> None:
        """Lock setup."""
        _ = self._check("#1")

    def request_key(self) -> tuple[int, int]:
        """Requests most recent key that was pressed.

        Returns:
            The key that was most recently pressed and the number of key presses
                that occurred since the last time this method was called.
        """
        a, b = self.query("?KY").split(",")
        return int(a), int(b)

    def reset_status(self) -> None:
        """Send the reset/status command."""
        _ = self._check("RE")

    def set_access_channel(self, channel: Literal[1, 2], setpoint: float, *, enable: bool) -> float:
        """Set the setpoint and the state of the valve for a channel.

        Args:
            channel: The channel number.
            setpoint: The setpoint value.
            enable: Whether to enable (`True`) or disable (`False`) the valve.

        Returns:
            The actual setpoint value.
        """
        self._check_channel(channel)
        state = "ON" if enable else "OFF"
        return float(self._check(f"AC{channel},{setpoint},{state}"))

    def set_actual_value(self, channel: Literal[1, 2], setpoint: float) -> float:
        """Set the actual value of a channel.

        Args:
            channel: The channel number.
            setpoint: The setpoint.

        Returns:
            The actual value.
        """
        self._check_channel(channel)
        return float(self.query(f"AV{channel},{setpoint}"))

    def set_address(self, address: int) -> None:
        """Set the address.

        Args:
            address: The address [0, 31].
        """
        if address < 0 or address > 31:  # noqa: PLR2004
            msg = f"Invalid address {address}, must be between [0, 31]"
            raise ValueError(msg)

        _ = self._check(f"AD,{address}")

    def set_dead_band(self, channel: Literal[1, 2], band: float) -> None:
        """Set the dead band of a channel.

        Args:
            channel: The channel number.
            band: The dead band (0.0% to 9.9% of full scale).
        """
        self._check_channel(channel)
        _ = self._check(f"DB{channel},{band}")

    def set_dialog(self, index: int) -> None:
        """Set the display dialog.

        Args:
            index: The dialog index [0, 29]. See Appendix D of the manual for more information.
        """
        if index < 0 or index > 29:  # noqa: PLR2004
            msg = f"Invalid dialog index {index}, must be in the range [0, 29]"
            raise ValueError(msg)
        _ = self._check(f"DG,{index}")

    def set_display_text(self, text: str, *, clear: bool = True) -> None:
        """Set the display text.

        To view the text on the display you must call
        [set_dialog][msl.equipment_resources.mks.pr4000b.PR4000B.set_dialog]
        with the index equal to 3.

        Args:
            text: The text to display. Maximum 32 characters.
            clear: Whether to clear the current display text before setting the new text.
        """
        if len(text) > 32:  # noqa: PLR2004
            msg = f"The display text must be <= 32 characters, got {text!r}"
            raise ValueError(msg)
        if clear:
            _ = self._check("!DT")
        _ = self._check(f"DT,{text}")

    def set_external_input_range(self, channel: Literal[1, 2], range: int) -> None:  # noqa: A002
        """Set the external input range of a channel.

        Args:
            channel: The channel number.
            range: The external input range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > MAX_RANGE:
            msg = f"Invalid external input range {range}"
            raise ValueError(msg)
        _ = self._check(f"EI{channel},{range}")

    def set_external_output_range(self, channel: Literal[1, 2], range: int) -> None:  # noqa: A002
        """Set the external output range of a channel.

        Args:
            channel: The channel number.
            range: The external output range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > MAX_RANGE:
            msg = f"Invalid external output range {range}"
            raise ValueError(msg)
        _ = self._check(f"EO{channel},{range}")

    def set_formula_relay(self, channel: Literal[1, 2], formula: str) -> None:
        """Set the relay formula of a channel.

        Args:
            channel: The channel number.
            formula: The relay formula.
        """
        self._check_channel(channel)
        _ = self._check(f"FR{channel},{formula}")

    def set_formula_temporary(self, channel: Literal[1, 2], formula: str) -> None:
        """Set the temporary formula of a channel.

        Args:
            channel: The channel number.
            formula: The temporary formula.
        """
        self._check_channel(channel)
        _ = self._check(f"FT{channel},{formula}")

    def set_gain(self, channel: Literal[1, 2], gain: float) -> None:
        """Set the gain of a channel.

        Args:
            channel: The channel number.
            gain: The gain [0.001, 2.000].
        """
        self._check_channel(channel)
        _ = self._check(f"GN{channel},{gain}")

    def set_input_range(self, channel: Literal[1, 2], range: int) -> None:  # noqa: A002
        """Set the input range of a channel.

        Args:
            channel: The channel number.
            range: The input range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > MAX_RANGE:
            msg = f"Invalid input range {range}"
            raise ValueError(msg)
        _ = self._check(f"IN{channel},{range}")

    def set_interface_mode(self, mode: int) -> None:
        """Set the interface mode.

        Args:
            mode: The interface mode.
        """
        _ = self._check(f"IM,{mode}")

    def set_limit_mode(self, channel: Literal[1, 2], mode: int | str | LimitMode) -> None:
        """Set the limit mode of a channel.

        Args:
            channel: The channel number.
            mode: The limit mode. Can be a [LimitMode][msl.equipment_resources.mks.pr4000b.LimitMode]
                member name or value. For example, `LimitMode.BAND`, `2`, or `"BAND"` are equivalent.
        """
        self._check_channel(channel)
        lm = to_enum(mode, LimitMode, to_upper=True)
        _ = self._check(f"LM{channel},{lm}")

    def set_linearization_point(self, channel: Literal[1, 2], point: int, x: float, y: float) -> None:
        """Set a point in the linearization table of a channel.

        Args:
            channel: The channel number.
            point: The point in the table [0, 10].
            x: The x value [-5% to 100% of full scale].
            y: The y value [-5% to 100% of full scale].
        """
        self._check_channel(channel)
        if point < 0 or point > MAX_POINT:
            msg = f"Invalid point {point}"
            raise ValueError(msg)
        _ = self._check(f"LN{channel},{point},{x},{y}")

    def set_linearization_size(self, channel: Literal[1, 2], size: int) -> None:
        """Set the size of the linearization table of a channel.

        Args:
            channel: The channel number.
            size: The size of the table.
        """
        self._check_channel(channel)
        if size < 0 or size > MAX_SIZE:
            msg = f"Invalid size {size}"
            raise ValueError(msg)
        _ = self._check(f"LS{channel},{size}")

    def set_lower_limit(self, channel: Literal[1, 2], limit: float) -> None:
        """Set the lower limit of a channel.

        Args:
            channel: The channel number.
            limit: The lower limit [-5% to 110% of full scale].
        """
        self._check_channel(channel)
        _ = self._check(f"LL{channel},{limit}")

    def set_offset(self, channel: Literal[1, 2], offset: int) -> None:
        """Set the offset of a channel.

        Args:
            channel: The channel number.
            offset: The offset [-250, 250].
        """
        self._check_channel(channel)
        if offset < -MAX_OFFSET or offset > MAX_OFFSET:
            msg = f"Invalid offset {offset}, must be between [-{MAX_OFFSET}, {MAX_OFFSET}]"
            raise ValueError(msg)
        _ = self._check(f"OF{channel},{offset}")

    def set_output_range(self, channel: Literal[1, 2], range: int) -> None:  # noqa: A002
        """Set the output range of a channel.

        Args:
            channel: The channel number.
            range: The output range [1, 10] in Volts.
        """
        self._check_channel(channel)
        if range < 1 or range > MAX_RANGE:
            msg = f"Invalid output range {range}"
            raise ValueError(msg)
        _ = self._check(f"OT{channel},{range}")

    def set_range(self, channel: Literal[1, 2], range: float, unit: int | str) -> None:  # noqa: A002
        """Set the range and unit of a channel.

        Args:
            channel: The channel number.
            range: The range value.
            unit: The unit as either an index number [0, 20] or a name (e.g., `7` or `"kPa"`).
                See [UNIT][msl.equipment_resources.mks.pr4000b.UNIT] for the supported unit values.
        """
        self._check_channel(channel)
        index = -1
        if isinstance(unit, str):
            lower = unit.lower()
            for i, v in enumerate(UNIT.values()):
                if v.lower() == lower:
                    index = i
                    break
        elif unit in UNIT:
            index = unit

        if index == -1:
            msg = f"Invalid unit {unit!r}"
            raise ValueError(msg)

        _ = self._check(f"RG{channel},{range},{index}")

    def set_relays(self, channel: Literal[1, 2], *, enable: bool) -> None:
        """Set the relay state of a channel.

        Args:
            channel: The channel number.
            enable: Whether to enable or disable the relay.
        """
        self._check_channel(channel)
        state = "ON" if enable else "OFF"
        _ = self._check(f"RL{channel},{state}")

    def set_remote_mode(self, *, enable: bool) -> None:
        """Set the remote operation mode to be enable or disabled.

        Args:
            enable: Whether to enable or disable remote operation.
        """
        mode = "ON" if enable else "OFF"
        _ = self._check(f"RT,{mode}")

    def set_resolution(self, *, enable: bool) -> None:
        """Set the 16-bit resolution to be enabled or disabled.

        Args:
            enable: Whether to enable or disable 16-bit resolution.
        """
        state = "ON" if enable else "OFF"
        _ = self._check(f"RS,{state}")

    def set_rtd_offset(self, channel: Literal[1, 2], offset: int) -> None:
        """Set the RTD offset of a channel.

        Args:
            channel: The channel number.
            offset: The RTD offset [-250, 250].
        """
        self._check_channel(channel)
        if offset < -MAX_OFFSET or offset > MAX_OFFSET:
            msg = f"Invalid RTD offset {offset}, must be between [-{MAX_OFFSET}, {MAX_OFFSET}]"
            raise ValueError(msg)
        _ = self._check(f"RO{channel},{offset}")

    def set_scale(self, channel: Literal[1, 2], scale: float) -> None:
        """Set the scale of a channel.

        Args:
            channel: The channel number.
            scale: The scale.
        """
        self._check_channel(channel)
        _ = self._check(f"SC{channel},{scale}")

    def set_setpoint(self, channel: Literal[1, 2], setpoint: float) -> None:
        """Set the setpoint of a channel.

        Args:
            channel: The channel number.
            setpoint: The setpoint.
        """
        self._check_channel(channel)
        _ = self._check(f"SP{channel},{setpoint}")

    def set_signal_mode(self, channel: Literal[1, 2], mode: SignalMode) -> None:
        """Set the range and unit of a channel.

        Args:
            channel: The channel number.
            mode: The signal mode. Can be a [SignalMode][msl.equipment_resources.mks.pr4000b.SignalMode]
                member name or value. For example, `SignalMode.OFF`, `1`, or `"OFF"` are equivalent.
        """
        self._check_channel(channel)
        sm = to_enum(mode, SignalMode, to_upper=True)
        _ = self._check(f"SM{channel},{sm}")

    def set_tweak_control(self, *, enable: bool) -> None:
        """Set tweak control.

        Args:
            enable: Whether to switch tweak control on or off.
        """
        _ = self._check("$1" if enable else "$0")

    def set_upper_limit(self, channel: Literal[1, 2], limit: float) -> None:
        """Set the upper limit of a channel.

        Args:
            channel: The channel number.
            limit: The upper limit [-5% to 110% of full scale].
        """
        self._check_channel(channel)
        _ = self._check(f"UL{channel},{limit}")

    def set_valve(self, channel: Literal[1, 2], *, enable: bool) -> None:
        """Set the state of the valve of a channel.

        Args:
            channel: The channel number.
            enable: Whether to enable or disable the valve state.
        """
        if channel == 0:  # pyright: ignore[reportUnnecessaryComparison]
            msg = (  # pyright: ignore[reportUnreachable]
                "The manual indicates that you can specify channel=0 "
                "to set both valves simultaneously, but that does not work"
            )
            raise ValueError(msg)

        self._check_channel(channel)
        state = "ON" if enable else "OFF"
        _ = self._check(f"VL{channel},{state}")

    def status(self) -> int:
        """Request status bits.

        Returns:
            The status value.
        """
        return int(self.query("ST"))

    def unlock(self) -> None:
        """Unlock setup."""
        _ = self._check("#0")

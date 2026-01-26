"""Connect to an MX100QP, MX100TP, MX103QP or MX180TP DC power supply from [Aim and Thurlby Thandar Instruments].

[Aim and Thurlby Thandar Instruments]: https://www.aimtti.com/
"""

# cSpell: ignore DECI DECV DELTAI DELTAV VRANGE INCI INCV OPALL TRIPRST ONACTION ONDELAY OFFACTION OFFDELAY
# cSpell: ignore Thandar handar hurlby nstruments
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from msl.equipment_resources.multi_message_based import MultiMessageBased

from msl.equipment.interfaces import MSLConnectionError

if TYPE_CHECKING:
    from typing import Literal

    from msl.equipment.schema import Equipment


EXECUTION_ERROR_CODES = {
    0: ("OK", "No error has occurred since this register was last read."),
    100: (
        "NumericError",
        "The parameter value sent was outside the permitted range for the command in the present circumstances.",
    ),
    102: (
        "RecallError",
        "A recall of set up data has been requested but the store specified does not contain any data.",
    ),
    103: (
        "CommandInvalid",
        (
            "The command is recognised but is not valid in the current circumstances. "
            "Typical examples would be trying to change V2 directly while the outputs are "
            "in voltage tracking mode with V1 as the master."
        ),
    ),
    104: (
        "RangeChangeError",
        (
            "An operation requiring a range change was requested but could not be completed. "
            "Typically this occurs because >0.5V was still present on output 1 and/or output 2 "
            "terminals at the time the command was executed."
        ),
    ),
    200: (
        "AccessDenied",
        (
            "An attempt was made to change the instrument's settings from an interface which is "
            "locked out of write privileges by a lock held by another interface."
        ),
    ),
}


class MXSeries(
    MultiMessageBased,
    manufacturer=r"Aim\s*[-&_]?\s*(and)?\s*T(hurlby)?\s*T(handar)?\s*I(nstruments)?",
    model=r"MX1[80][03][TQ]P",
    flags=re.IGNORECASE,
):
    """Connect to an MX100QP, MX100TP, MX103QP or MX180TP DC power supply."""

    def __init__(self, equipment: Equipment) -> None:
        r"""Connect to an MX100QP, MX100TP, MX103QP or MX180TP DC power supply from [Aim and Thurlby Thandar Instruments].

        [Aim and Thurlby Thandar Instruments]: https://www.aimtti.com/

        Regular-expression patterns that are used to select this Resource when
        [connect()][msl.equipment.schema.Equipment.connect] is called.
        ```python
        manufacturer=r"Aim\s*[-&_]?\s*(and)?\s*T(hurlby)?\s*T(handar)?\s*I(nstruments)?"
        model=r"MX1[80][03][TQ]P"
        flags=IGNORECASE
        ```

        Args:
            equipment: An [Equipment][] instance.
        """  # noqa: E501
        super().__init__(equipment)
        self.rstrip: bool = True

    def _check_event_status_register(self, command: str) -> None:
        """Check the value of the standard event status register for an error.

        Args:
            command: The command that was sent prior to checking for an error.
        """
        status = self.event_status_register()
        # Bit 7 - Power On. Set when power is first applied to the instrument.
        # Bit 1 and 6 - Not used, permanently 0.
        # Bit 0 - Operation Complete. Set in response to the *OPC command.
        if status & (1 << 5):  # Bit 5 - Command Error
            err_type = "CommandError"
            err_msg = "A syntax error is detected in a command or parameter"
        elif status & (1 << 4):  # Bit 4 - Execution Error
            code = int(self.query("EER?"))
            err_type, err_msg = EXECUTION_ERROR_CODES.get(code, ("UndefinedError", f"Unknown error code {code}"))
        elif status & (1 << 3):  # Bit 3 - Verify Timeout Error
            err_type = "VerifyTimeoutError"
            err_msg = (
                "A parameter has been set with 'verify' specified and the value has not been reached within 5 seconds, "
                "e.g., the output voltage is slowed by a load with a large capacitance"
            )
        elif status & (1 << 2):  # Bit 2 - Query Error
            err_type = "QueryError"
            err_msg = "The controller has not issued commands and read response messages in the correct sequence"
        else:
            return

        raise MSLConnectionError(self, f"{err_type}: {err_msg} -> command={command!r}")

    def _query_and_check(self, command: str) -> str:
        """Query the command. If there is an error when querying then check the event status register for an error."""
        try:
            return self.query(command)
        except:
            self._check_event_status_register(command)
            # if checking the event status register does not raise an exception
            # then raise the query exception
            raise

    def _write_and_check(self, command: str) -> None:
        """Write the command and check the event status register for an error."""
        _ = self.write(command)
        self._check_event_status_register(command)

    def clear(self) -> None:
        """Send the clear command, `*CLS`."""
        _ = self.write("*CLS")

    def decrement_current(self, channel: int) -> None:
        """Decrement the current limit by step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
        """
        self._write_and_check(f"DECI{channel}")

    def decrement_voltage(self, channel: int, *, verify: bool = True) -> None:
        """Decrement the voltage by step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            verify: Whether to verify that the output voltage has stabilized at
                the decremented voltage before returning to the calling program.
        """
        v = "V" if verify else ""
        self._write_and_check(f"DECV{channel}{v}")

    def event_status_register(self) -> int:
        """Read and clear the standard event status register.

        Returns:
            The event status register value.
        """
        return int(self.query("*ESR?"))

    def get_current(self, channel: int) -> float:
        """Get the output current of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            The output current (in Amps).
        """
        reply = self._query_and_check(f"I{channel}O?")
        return float(reply[:-1])  # the reply ends with 'A'

    def get_current_limit(self, channel: int) -> float:
        """Get the current limit of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            The current limit (in Amps).
        """
        reply = self._query_and_check(f"I{channel}?")
        return float(reply[2:])

    def get_current_step_size(self, channel: int) -> float:
        """Get the current limit step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            The current limit step size (in Amps).
        """
        reply = self._query_and_check(f"DELTAI{channel}?")
        return float(reply[7:])

    def get_over_current_protection(self, channel: int) -> float | None:
        """Get the over-current protection trip point of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            If the trip point is enabled then returns the trip point value in Amps.
            Otherwise, returns `None` if the over-current protection is disabled.
        """
        reply = self._query_and_check(f"OCP{channel}?")
        if reply.endswith("OFF"):
            return None
        return float(reply[3:])

    def get_over_voltage_protection(self, channel: int) -> float | None:
        """Get the over-voltage protection trip point of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            If the trip point is enabled then returns the trip point value in Volts.
            Otherwise, returns `None` if the over-voltage protection is disabled.
        """
        reply = self._query_and_check(f"OVP{channel}?")
        if reply.endswith("OFF"):
            return None
        return float(reply[3:])

    def get_voltage(self, channel: int) -> float:
        """Get the output voltage of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            The output voltage (in Volts).
        """
        reply = self._query_and_check(f"V{channel}O?")
        return float(reply[:-1])  # the reply ends with 'V'

    def get_voltage_range(self, channel: int) -> int:
        """Get the output voltage range index of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            The output voltage range index. See the manual for more details.
            For example, 2 &#8594; 35V/3A.
        """
        return int(self._query_and_check(f"VRANGE{channel}?"))

    def get_voltage_setpoint(self, channel: int) -> float:
        """Get the set-point voltage of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            The set-point voltage (in Volts).
        """
        reply = self._query_and_check(f"V{channel}?")
        return float(reply[2:])

    def get_voltage_step_size(self, channel: int) -> float:
        """Get the voltage step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            The voltage step size (in Volts).
        """
        reply = self._query_and_check(f"DELTAV{channel}?")
        return float(reply[7:])

    def get_voltage_tracking_mode(self) -> int:
        """Get the voltage tracking mode of the unit.

        Returns:
            The voltage tracking mode. See the manual for more details.
        """
        return int(self._query_and_check("CONFIG?"))

    def increment_current(self, channel: int) -> None:
        """Increment the current limit by the step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
        """
        self._write_and_check(f"INCI{channel}")

    def increment_voltage(self, channel: int, *, verify: bool = True) -> None:
        """Increment the voltage by the step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            verify: Whether to verify that the output voltage has stabilized at
                the incremented voltage before returning to the calling program.
        """
        v = "V" if verify else ""
        self._write_and_check(f"INCV{channel}{v}")

    def is_output_on(self, channel: int) -> bool:
        """Check if the output channel is on or off.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).

        Returns:
            Whether the output channel is on or off.
        """
        reply = self._query_and_check(f"OP{channel}?")
        return reply == "1"

    def recall(self, channel: int, index: int) -> None:
        """Recall the settings of the output channel from the store.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            index: The store index number, can be 0-49.
        """
        self._write_and_check(f"RCL{channel} {index}")

    def recall_all(self, index: int) -> None:
        """Recall the settings for all output channels from the store.

        Args:
            index: The store index number, can be 0-49.
        """
        self._write_and_check(f"*SAV {index}")

    def reset(self) -> None:
        """Send the reset command, `*RST`."""
        _ = self.write("*RST")

    def reset_trip(self) -> None:
        """Attempt to clear all trip conditions."""
        _ = self.write("TRIPRST")

    def save(self, channel: int, index: int) -> None:
        """Save the present settings of the output channel to the store.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            index: The store index number, can be 0-49.
        """
        self._write_and_check(f"SAV{channel} {index}")

    def save_all(self, index: int) -> None:
        """Save the settings of all output channels to the store.

        Args:
            index: The store index number, can be 0-49.
        """
        self._write_and_check(f"*RCL {index}")

    def set_current_limit(self, channel: int, value: float) -> None:
        """Set the current limit of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            value: The current limit (in Amps).
        """
        self._write_and_check(f"I{channel} {value}")

    def set_current_meter_averaging(self, channel: int, mode: Literal["ON", "OFF", "LOW", "MED", "HIGH"]) -> None:
        """Set the current meter measurement averaging of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            mode: Averaging mode.
        """
        self._write_and_check(f"DAMPING{channel} {mode}")

    def set_current_step_size(self, channel: int, size: float) -> None:
        """Set the current limit step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            size: The current limit step size, in Amps.
        """
        self._write_and_check(f"DELTAI{channel} {size}")

    def set_multi_off_action(self, channel: int, action: Literal["QUICK", "NEVER", "DELAY"]) -> None:
        """Set the Multi-Off action of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            action: The Multi-Off action.
        """
        self._write_and_check(f"OFFACTION{channel} {action}")

    def set_multi_off_delay(self, channel: int, delay: int) -> None:
        """Set the Multi-Off delay, in milliseconds, of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            delay: The turn-off delay (in milliseconds).
        """
        self._write_and_check(f"OFFDELAY{channel} {delay}")

    def set_multi_on_action(self, channel: int, action: Literal["QUICK", "NEVER", "DELAY"]) -> None:
        """Set the Multi-On action of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            action: The Multi-On action.
        """
        self._write_and_check(f"ONACTION{channel} {action}")

    def set_multi_on_delay(self, channel: int, delay: int) -> None:
        """Set the Multi-On delay, in milliseconds, of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            delay: The turn-on delay (in milliseconds).
        """
        self._write_and_check(f"ONDELAY{channel} {delay}")

    def set_over_current_protection(self, channel: int, *, enable: bool, value: float | None = None) -> None:
        """Set the over-current protection trip point of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            enable: Whether to enable or disable the over-current protection trip point.
            value: If the trip point is enabled then you must specify a value (in Amps).
        """
        if enable:
            if value is None:
                msg = "Must specify the trip point value if the trip point is enabled"
                raise ValueError(msg)
            command = f"OCP{channel} ON;OCP{channel} {value}"
        else:
            command = f"OCP{channel} OFF"
        self._write_and_check(command)

    def set_over_voltage_protection(self, channel: int, *, enable: bool, value: float | None = None) -> None:
        """Set the over-voltage protection trip point of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            enable: Whether to enable or disable the over-voltage protection trip point.
            value: If the trip point is enabled then you must specify a value (in Volts).
        """
        if enable:
            if value is None:
                msg = "Must specify the trip point value if the trip point is enabled"
                raise ValueError(msg)
            command = f"OVP{channel} ON;OVP{channel} {value}"
        else:
            command = f"OVP{channel} OFF"
        self._write_and_check(command)

    def set_voltage(self, channel: int, value: float, *, verify: bool = True) -> None:
        """Set the output voltage of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            value: The value (in Volts).
            verify: Whether to verify that the output voltage has stabilized at `value`
                before returning to the calling program.
        """
        command = f"V{channel}V {value}" if verify else f"V{channel} {value}"
        self._write_and_check(command)

    def set_voltage_range(self, channel: int, index: int) -> None:
        """Set the output voltage range of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            index: The output voltage range index. See the manual for more details.
                For example, 2 &#8594; 35V/3A.
        """
        self._write_and_check(f"VRANGE{channel} {index}")

    def set_voltage_step_size(self, channel: int, size: float) -> None:
        """Set the voltage step size of the output channel.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
            size: The voltage step size (in Volts).
        """
        self._write_and_check(f"DELTAV{channel} {size}")

    def set_voltage_tracking_mode(self, mode: int) -> None:
        """Set the voltage tracking mode of the unit.

        Args:
            mode: The voltage tracking mode. See the manual for more details.
        """
        self._write_and_check(f"CONFIG {mode}")

    def turn_off(self, channel: int) -> None:
        """Turn the output channel off.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
        """
        self._write_and_check(f"OP{channel} 0")

    def turn_off_multi(self, options: dict[int, bool | int] | None = None) -> None:
        """Turn multiple output channels off (the Multi-Off feature).

        Args:
            options: Set the Multi-Off option for each output channel before setting Multi-Off.
                If not specified then uses the pre-programmed options. If a particular output
                channel is not included in `options` then uses the pre-programmed option for
                that channel. The keys are the output channel number and the value can be
                `False` (set the channel to `NEVER`, see the manual for more details),
                `True` (set the channel to `QUICK`, see the manual for more details) or a
                delay in milliseconds (as an [int][]). Examples,

                * `{1: False}` &#8594; channel 1 does not turn off
                * `{2: 100}` &#8594; channel 2 has a 100-ms delay
                * `{1: 100, 3: True}` &#8594; channel 1 has a 100-ms delay and channel 3 turns off immediately
                * `{1: 100, 2: 200, 3: 300}` &#8594; channel 1 has a 100-ms delay, channel 2 has a 200-ms delay
                    and channel 3 has a 300-ms delay
        """
        if options:
            for channel, value in options.items():
                if isinstance(value, bool):
                    self.set_multi_off_action(channel, "QUICK" if value else "NEVER")
                else:
                    self.set_multi_off_action(channel, "DELAY")
                    self.set_multi_off_delay(channel, value)
                    time.sleep(0.1)  # otherwise the power supply may not set the delay properly
        self._write_and_check("OPALL 0")

    def turn_on(self, channel: int) -> None:
        """Turn the output channel on.

        Args:
            channel: The output channel. The first output channel is 1 (not 0).
        """
        self._write_and_check(f"OP{channel} 1")

    def turn_on_multi(self, options: dict[int, bool | int] | None = None) -> None:
        """Turn multiple output channels on (the Multi-On feature).

        Args:
            options: Set the Multi-On option for each output channel before setting Multi-On.
                If not specified then uses the pre-programmed options. If a particular output
                channel is not included in `options` then uses the pre-programmed option for
                that channel. The keys are the output channel number and the value can be
                `False` (set the channel to `NEVER`, see the manual for more details),
                `True` (set the channel to `QUICK`, see the manual for more details) or a
                delay in milliseconds (as an [int][]). Examples,

                * `{1: False}` &#8594; channel 1 does not turn on
                * `{2: 100}` &#8594; channel 2 has a 100-ms delay
                * `{1: 100, 3: True}` &#8594;` channel 1 has a 100-ms delay and channel 3 turns on immediately
                * `{1: 100, 2: 200, 3: 300}` &#8594; channel 1 has a 100-ms delay, channel 2 has a 200-ms delay
                    and channel 3 has a 300-ms delay
        """
        if options:
            for channel, value in options.items():
                if isinstance(value, bool):
                    self.set_multi_on_action(channel, "QUICK" if value else "NEVER")
                else:
                    self.set_multi_on_action(channel, "DELAY")
                    self.set_multi_on_delay(channel, value)
                    time.sleep(0.1)  # otherwise the power supply may not set the delay properly
        self._write_and_check("OPALL 1")

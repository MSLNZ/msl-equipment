"""Communicate with the EQ-99 Manager from [Energetiq](https://www.energetiq.com/)."""

# cSpell: words REMERR EXPMODE LAMPTIME SHUTINIT TRIGMODE
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from msl.equipment.interfaces import MSLConnectionError, Serial

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment

MIN_EXPOSURE_TIME = 100  # ms
MAX_TIME = 30000  # ms
MAX_RUNTIME = 9999  # hours


class EQ99(Serial, manufacturer=r"Energetiq", model=r"EQ-99(-MGR)?", flags=re.IGNORECASE):
    """Communicate with the EQ-99 Manager from [Energetiq](https://www.energetiq.com/)."""

    def __init__(self, equipment: Equipment) -> None:
        """Communicate with the EQ-99 Manager from Energetiq.

        Args:
            equipment: An [Equipment][] instance.
        """
        assert equipment.connection is not None  # noqa: S101
        equipment.connection.properties.setdefault("baud_rate", 38400)
        super().__init__(equipment)
        self.rstrip: bool = True

    def identity(self) -> str:
        """Query the instrument identification.

        Returns:
            Returns the identification string for the instrument in the following format:
                *Energetiq Model SN Ver Build*
        """
        return self.query("*IDN?")

    def reset(self) -> None:
        """Resets the instrument to factory defaults and the output is shut off.

        The unit remains in remote mode.
        """
        _ = self._write_check("*RST")

    def get_beep(self) -> bool:
        """Query whether beeps are enabled.

        Returns:
            Whether beeps are enabled.
        """
        return bool(int(self.query("BEEP?")))

    def set_beep(self, beep: bool | int = 2) -> None:  # noqa: FBT001
        """Set the beep value.

        Args:
            beep: Causes the instrument to beep, or enables or disabled the beep
                sound for error messages and other events that generate and
                audible response.

                * 0 or `False` &mdash; Disable the beep sound
                * 1 or `True` &mdash; Enable the beep sound
                * 2 &mdash; Generate one beep
        """
        if beep not in [0, 1, 2, True, False]:
            msg = f"Invalid beep value '{beep}'"
            raise MSLConnectionError(self, msg)
        self._write_check(f"BEEP {beep}")

    def get_brightness(self) -> int:
        """Query the display brightness.

        Returns:
            Returns the value of the display brightness (between 0 and 100).
        """
        return int(self.query("BRIGHT?"))

    def set_brightness(self, brightness: int) -> None:
        """Set the display brightness.

        Args:
            brightness: Sets the display brightness level from 0 to 100 percent.
                There are only 8 brightness levels (each separated by about
                12.5 percent) and the brightness value is used to select an
                appropriate level.
        """
        self._write_check(f"BRIGHT {int(brightness)}")

    def delay(self, milliseconds: int) -> None:
        """Specify a delay to use in command processing.

        Args:
            milliseconds: Causes command processing to be delayed for the specified number
                of milliseconds. Valid range is from 1 to 30000 milliseconds.
        """
        if not (1 <= milliseconds <= MAX_TIME):
            msg = f"Invalid delay of {milliseconds} milliseconds, must be in range [1, {MAX_TIME}]"
            raise ValueError(msg)
        self._write_check(f"DELAY {milliseconds}")

    def condition_register(self) -> int:
        """Query the LDLS condition register.

        The condition register reflects the state of the instrument
        at the time the condition register is read.

        The bit-mask sequence is as follows:

        | Bit Index | Value | Description             |
        | :-------: | :---: | :---------------------- |
        |   0       |    1  | Interlock               |
        |   1       |    2  | Controller not detected |
        |   2       |    4  | Controller fault        |
        |   3       |    8  | Lamp fault              |
        |   4       |   16  | Output on               |
        |   5       |   32  | Lamp on                 |
        |   6       |   64  | Laser on                |
        |   7       |  128  | Laser stable            |
        |   8       |  256  | Shutter open            |

        Returns:
            The condition register value.
        """
        return int(self.query("LDLS:COND?"))

    def event_register(self) -> int:
        """Query the LDLS event register.

        Returns the LDLS event register. The event register reflects the
        occurrence of any condition since the last time the event register
        was read. For example, if the output was turned on and then turned off,
        the Output on the bit in the condition register will be zero, but the
        same bit in the event register will be one.

        The bit-mask sequence is as follows:

        | Bit Index | Value | Description             |
        | :-------: | :---: | :---------------------- |
        |   0       |    1  | Interlock               |
        |   1       |    2  | Controller not detected |
        |   2       |    4  | Controller fault        |
        |   3       |    8  | Lamp fault              |
        |   4       |   16  | Output on               |
        |   5       |   32  | Lamp on                 |
        |   6       |   64  | Laser on                |
        |   7       |  128  | Laser stable            |
        |   8       |  256  | Shutter open            |

        Returns:
            The event register value.
        """
        return int(self.query("LDLS:EVENT?"))

    def get_exposure_time(self) -> int:
        """Query the exposure time.

        Returns:
            The exposure time, in milliseconds.
        """
        return int(self.query("LDLS:EXPOSURE?"))

    def set_exposure_time(self, milliseconds: int) -> None:
        """Set the exposure time.

        Exposure time is used when the shutter exposure mode is set to `Exposure mode`
        (see [set_exposure_mode][msl.equipment_resources.energetiq.eq99.EQ99.set_exposure_mode]).
        An exposure is triggered by a shutter button press or the shutter trigger input.

        Args:
            milliseconds: The exposure time, in milliseconds, from 100 to 30000 ms.
        """
        if not (MIN_EXPOSURE_TIME <= milliseconds <= MAX_TIME):
            msg = (
                f"Invalid exposure time of {milliseconds} milliseconds, "
                f"must be in range [{MIN_EXPOSURE_TIME}, {MAX_TIME}]"
            )
            raise ValueError(msg)
        self._write_check(f"LDLS:EXPOSURE {milliseconds}")

    def get_exposure_mode(self) -> int:
        """Query the exposure mode.

        Returns:
            The exposure mode.

                * 0 &mdash; Manual mode
                * 1 &mdash; Exposure mode
        """
        return int(self.query("LDLS:EXPMODE?"))

    def set_exposure_mode(self, mode: int) -> None:
        """Set the exposure mode.

        Same as the *Shutter* setting in the menu.

        Args:
            mode: The exposure mode.

                * 0 &mdash; Manual mode
                * 1 &mdash; Exposure mode
        """
        self._write_check(f"LDLS:EXPMODE {mode}")

    def get_output_state(self) -> bool:
        """Query the output state.

        Returns:
            Whether the output is enabled or disabled.
        """
        return bool(int(self.query("LDLS:OUTPUT?")))

    def set_output_state(self, enable: bool) -> None:  # noqa: FBT001
        """Turn the output on or off.

        Args:
            enable: Whether to enable or disable the output.
        """
        self._write_check(f"LDLS:OUTPUT {enable}")

    def get_lamp_runtime(self) -> float:
        """Query the lamp runtime.

        Returns:
            The number of hours accumulated while the lamp was on.
        """
        return float(self.query("LDLS:LAMPTIME?"))

    def set_lamp_runtime(self, hours: float) -> None:
        """Set the lamp runtime.

        Resets the runtime to the new value. Useful for resetting the runtime
        to zero when the lamp has been serviced or replaced, or when moving
        the manager to a new LDLS system.

        Args:
            hours: The lamp runtime, in hours, between 0 and 9999.
        """
        if not (0 <= hours <= MAX_RUNTIME):
            msg = f"Invalid lamp runtime of {hours} hours, must be in range [0, {MAX_RUNTIME}]"
            raise ValueError(msg)
        self._write_check(f"LDLS:LAMPTIME {hours}")

    def get_shutter_power_up_state(self) -> bool:
        """Query the power-up shutter state.

        Returns:
            The power-up shutter state.

                * `False` &mdash; Shutter is closed on power-up
                * `True` &mdash; Shutter is open on power-up
        """
        return bool(int(self.query("LDLS:SHUTINIT?")))

    def set_shutter_power_up_state(self, state: bool) -> None:  # noqa: FBT001
        """Set the power-up shutter state.

        Args:
            state: Sets the initial state of the shutter on power-up of the manager.

                * `False` &mdash; Shutter is closed on power-up
                * `True` &mdash; Shutter is open on power-up
        """
        self._write_check(f"LDLS:SHUTINIT {state}")

    def get_shutter_state(self) -> bool:
        """Query the shutter state.

        Returns:
            The state of the shutter.

                * `False` &mdash; Shutter is closed
                * `True` &mdash; Shutter is open
        """
        return bool(int(self.query("LDLS:SHUTTER?")))

    def set_shutter_state(self, state: bool) -> None:  # noqa: FBT001
        """Open, close, or trigger the shutter.

        A close command (state is `False`) will always close the shutter,
        regardless of exposure mode. An open command (state is `True`)
        will open the shutter if exposure mode is set to *Manual*, or
        trigger a shutter if exposure mode is set to *Exposure*.

        Args:
            state: The state of the shutter.

                * `False` &mdash; Close the shutter
                * `True` &mdash; Open or trigger the shutter
        """
        self._write_check(f"LDLS:SHUTTER {state}")

    def get_trigger_mode(self) -> int:
        """Query the trigger mode.

        Returns:
            The trigger mode. See [set_trigger_mode][msl.equipment_resources.energetiq.eq99.EQ99.set_trigger_mode]
                for more details.
        """
        return int(self.query("LDLS:TRIGMODE?"))

    def set_trigger_mode(self, mode: int) -> None:
        """Set the trigger mode.

        The trigger mode controls how the shutter trigger input controls the
        operation of the shutter. For more information on trigger modes, see
        *Shutter Operation* in the *Operating the Instrument* section of the
        manual for more details.

        Args:
            mode: The trigger mode.

                * 0 &mdash; Positive edge trigger
                * 1 &mdash; Negative edge trigger
                * 2 &mdash; Positive level trigger
                * 3 &mdash; Negative level trigger
                * 4 &mdash; Off (trigger disabled)
        """
        self._write_check(f"LDLS:TRIGMODE {mode}")

    def get_message_buffer(self) -> str:
        """Query the internal message buffer.

        Returns:
            The value of the internal message buffer.
        """
        return self.query("MESSAGE?")

    def set_message_buffer(self, message: str) -> None:
        """Set the message buffer.

        Args:
            message: Sets the internal message buffer, up to a maximum of 16 characters. If more than
                16 characters are specified then the additional characters are silently ignored.
        """
        self._write_check(f"MESSAGE {message}")

    def get_remote_mode_error(self) -> bool:
        """Query whether errors are displayed while in remote mode.

        Returns:
            Whether errors are displayed while in remote mode.
        """
        return bool(int(self.query("REMERR?")))

    def set_remote_mode_error(self, enable: bool | int) -> None:  # noqa: FBT001
        """Set whether to display errors while in remote mode.

        This command controls if the instrument will display errors while in
        remote mode. If set to `0`/`False`, then errors will not be displayed. If
        set to `1`/`True`, errors will be displayed. Errors will always accumulate
        in the error queue.

        Args:
            enable: Whether to display errors while in remote mode.

                * 0 or `False` &mdash; Do not display errors in remote mode
                * 1 or `True` &mdash; Display errors in remote mode
        """
        self._write_check(f"REMERR {enable}")

    def serial_number(self) -> str:
        """Query the serial number of the instrument.

        Returns:
            The serial number of the instrument. This is the same information that is part of the `*IDN?` query.
        """
        return self.query("SN?")

    def get_termination(self) -> int:
        """Query response terminator.

        Returns the current response terminator setting. See
        [set_termination][msl.equipment_resources.energetiq.eq99.EQ99.set_termination]
        for possible return values.

        Returns:
            The response terminator.
        """
        return int(self.query("TERM?"))

    def set_termination(self, value: int) -> None:
        """Set the response terminator character(s).

        This command controls the termination characters used for
        responses to queries.

        Args:
            value: The response terminator character(s).

                * 0 or 1 &mdash; `<CR><LF>`
                * 2 or 3 &mdash; `<CR>`
                * 4 or 5 &mdash; `<LF>`
                * 6 or 7 &mdash; no terminator
        """
        self._write_check(f"TERM {value}")

    def unit_runtime(self) -> str:
        """Query unit run time.

        Returns:
            Returns the elapsed time since the unit has been turned on.
                Format is in HH:MM:SS.ss, where HH is hours, MM is minutes,
                SS is seconds, and ss is hundredths of a second.
        """
        return self.query("TIME?")

    def timer(self) -> str:
        """Query the elapsed time since the last time this method was called.

        Returns:
            Returns the elapsed time since the last time this method was
                called, or, if this is the first time calling this method
                then the time since unit has been turned on. Format is in
                HH:MM:SS.ss, where HH is hours, MM is minutes, SS is seconds,
                and ss is hundredths of a second.
        """
        return self.query("TIMER?")

    def version(self) -> str:
        """Query the firmware version.

        Returns:
            Returns the firmware version. This is the same information that is part of the `*IDN?` query.
        """
        return self.query("VER?")

    def _write_check(self, command: str) -> None:
        _ = self.write(command)
        message = self.query("ERRSTR?")
        if message == "0":
            return
        raise MSLConnectionError(self, message)

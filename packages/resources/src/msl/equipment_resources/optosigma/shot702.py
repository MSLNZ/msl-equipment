"""Two-axis stage controller (SHOT-702) from [OptoSigma](https://jp.optosigma.com/en_jp/){:target="_blank"}."""

# cSpell: ignore LMWK Koki
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, NamedTuple

from msl.equipment.interfaces import MSLConnectionError, Serial

if TYPE_CHECKING:
    from re import Pattern
    from typing import Callable, Literal

    from msl.equipment.schema import Equipment


class Mode(IntEnum):
    """The mode by which a stage can be be moved.

    Attributes:
        HAND (int): Move by hand, `0`.
        MOTOR (int): Move by motor, `1`.
    """

    HAND = 0
    MOTOR = 1


class State(Enum):
    """Stage stopped state.

    Attributes:
        L (str): Stage 1 stopped at a limit sensor.
        M (str): Stage 2 stopped at a limit sensor.
        W (str): Stage 1 and stage 2 stopped at a limit sensor.
        K (str): Normal stop.
    """

    L = "L"
    M = "M"
    W = "W"
    K = "K"


@dataclass
class Speed:
    """Speed settings.

    Args:
        minimum: Minimum speed (1 - 500k pulses/second).
        maximum: Maximum speed (1 - 500k pulses/second).
        acceleration: Acceleration (deceleration) time in milliseconds (1 - 1000 ms).
    """

    minimum: int
    maximum: int
    acceleration: int


class Status(NamedTuple):
    """The status of each stage.

    Attributes:
        position1: The current position of stage 1.
        position2: The current position of stage 2.
        state: The stopped state of the stage.
        is_moving: Whether a stage is busy moving.
    """

    position1: int
    position2: int
    state: State
    is_moving: bool


class SHOT702(Serial, manufacturer=r"Opto\s*Sigma|Sigma\s*Koki", model=r"SHOT-702"):
    """Two-axis stage controller (SHOT-702) from [OptoSigma](https://jp.optosigma.com/en_jp/){:target="_blank"}."""

    def __init__(self, equipment: Equipment) -> None:
        r"""Two-axis stage controller (SHOT-702) from OptoSigma.

        The default baud rate is set to 38400 and the read/write termination characters are `\r\n`.

        Args:
            equipment: An [Equipment][] instance.
        """
        assert equipment.connection is not None  # noqa: S101
        equipment.connection.properties.setdefault("baud_rate", 38400)
        super().__init__(equipment)

        self.read_termination: bytes = b"\r\n"
        self.write_termination: bytes = b"\r\n"

        self._status_regex: Pattern[str] = re.compile(r"(-*)\s*(\d+),(-*)\s*(\d+),([XK]),([LMWK]),([BR])")
        self._speed_regex: Pattern[str] = re.compile(r"S(\d+)F(\d+)R(\d+)S(\d+)F(\d+)R(\d+)")

    def _move(self, letter: str, stage: Literal[1, 2, "W"], *n_pulses: int) -> None:
        if not n_pulses:
            preposition = "by" if letter == "M" else "to"
            msg = f"You must specify at least 1 position to move {preposition}"
            raise ValueError(msg)

        cmd = f"{letter}:{stage}"
        for val in n_pulses:
            if val < 0:
                cmd += f"-P{abs(val)}"
            else:
                cmd += f"+P{val}"

        reply = self.query(cmd)
        if not reply.startswith("OK") or not self.query("G:").startswith("OK"):
            preposition = "by" if letter == "M" else "to"
            if stage == "W":
                msg = f"Cannot move stages {preposition} {n_pulses}"
            else:
                msg = f"Cannot move stage {stage} {preposition} {n_pulses[0]}"
            raise MSLConnectionError(self, msg)

    def _speed(self, letter: str, stage: Literal[1, 2, "W"], *speeds: Speed) -> None:
        if not speeds:
            msg = "You must specify at least 1 Speed argument"
            raise ValueError(msg)

        cmd = f"{letter}:{stage}"
        for speed in speeds:
            cmd += f"S{speed.minimum}F{speed.maximum}R{speed.acceleration}"

        if not self.query(cmd).startswith("OK"):
            msg = f"Cannot set stage {stage} speed to {speeds}"
            raise MSLConnectionError(self, msg)

    def get_input_status(self) -> int:
        """Get the I/O input connector status.

        Returns:
            Can either be 0 or 1 (see manual).
        """
        return int(self.query("I:"))

    def get_speed(self) -> tuple[Speed, Speed]:
        """Get the speed that each stage moves to a position.

        Returns:
            The speed of each stage, `(stage1, stage2)`.
        """
        reply = self.query("?:DW")
        match = self._speed_regex.match(reply)
        if match is None:
            msg = f"Invalid speed regex expression for the reply {reply!r}"
            raise MSLConnectionError(self, msg)

        a, b, c, d, e, f = map(int, match.groups())
        return Speed(a, b, c), Speed(d, e, f)

    def get_speed_origin(self) -> tuple[Speed, Speed]:
        """Get the speed that each stage moves to the origin.

        Returns:
            The speed of each stage, `(stage1, stage2)`.
        """
        reply = self.query("?:BW")
        match = self._speed_regex.match(reply)
        if match is None:
            msg = f"Invalid speed regex expression for the reply {reply!r}"
            raise MSLConnectionError(self, msg)

        a, b, c, d, e, f = map(int, match.groups())
        return Speed(a, b, c), Speed(d, e, f)

    def get_steps(self) -> tuple[int, int]:
        """Get the number of steps for each stage.

        Returns:
            The number of steps for `(stage1, stage2)`.
        """
        a, b = map(int, self.query("?:SW").split(","))
        return a, b

    def get_travel_per_pulse(self) -> tuple[float, float]:
        """Get the travel per pulse for each stage.

        Returns:
            The travel per pulse for `(stage1, stage2)`.
        """
        a, b = map(float, self.query("?:PW").split(","))
        return a, b

    def get_version(self) -> str:
        """Get the firmware version number.

        Returns:
            The version number.
        """
        return self.query("?:V").rstrip()

    def home(self, stage: Literal[1, 2, "W"]) -> None:
        """Move the stage(s) to the home position.

        Args:
            stage: The stage(s) to home.

                * `1` &mdash; home stage 1
                * `2` &mdash; home stage 2
                * `"W"` &mdash; home stages 1 and 2
        """
        reply = self.query(f"H:{stage}")
        if not reply.startswith("OK"):
            msg = f"Cannot home stage {stage}"
            raise MSLConnectionError(self, msg)

    def is_moving(self) -> bool:
        """Check if a stage is busy moving.

        Returns:
            Whether a stage is busy moving.
        """
        return self.query("!:").startswith("B")

    def move(self, stage: Literal[1, 2, "W"], direction: Literal["+", "-", "++", "+-", "-+", "--"]) -> None:
        """Start moving the stage(s), at the minimum speed, in the specified direction.

        Args:
            stage: The stage(s) to move.

                * `1` &mdash; move stage 1
                * `2` &mdash; move stage 2
                * `"W"` &mdash; move stages 1 and 2

            direction: The direction that the stage(s) should move.

                * `"+"` &mdash; move a single stage in the `+` direction
                * `"-"` &mdash; move a single stage in the `-` direction
                * `"++"` &mdash; move stage 1 in the `+` direction, stage 2 in the `+` direction
                * `"+-"` &mdash; move stage 1 in the `+` direction, stage 2 in the `-` direction
                * `"-+"` &mdash; move stage 1 in the `-` direction, stage 2 in the `+` direction
                * `"--"` &mdash; move stage 1 in the `-` direction, stage 2 in the `-` direction
        """
        reply = self.query(f"J:{stage}{direction}")
        if not reply.startswith("OK") or not self.query("G:").startswith("OK"):
            msg = f"Cannot move stage {stage} in direction={direction!r}"
            raise MSLConnectionError(self, msg)

    def move_absolute(self, stage: Literal[1, 2, "W"], *position: int) -> None:
        """Move the stage(s) to the specified position.

        Args:
            stage: The stage(s) to move.

                * `1` &mdash; move stage 1
                * `2` &mdash; move stage 2
                * `"W"` &mdash; move stages 1 and 2

            position: The position the stage(s) should move to.

        !!! example
            * `move_absolute(1, 1000)` &mdash; move stage 1 to position 1000 in the `+` direction
            * `move_absolute(2, -5000)` &mdash; move stage 2 to position 5000 in the `-` direction
            * `move_absolute('W', 1000, -5000)` &mdash; move stage 1 to position 1000 in the `+` direction, and
                move stage 2 to position 5000 in the `-` direction
        """
        self._move("A", stage, *position)

    def move_relative(self, stage: Literal[1, 2, "W"], *num_pulses: int) -> None:
        """Move the stage(s) by a relative amount.

        Args:
            stage: The stage(s) to move.

                * `1` &mdash; move stage 1
                * `2` &mdash; move stage 2
                * `"W"` &mdash; move stages 1 and 2

            num_pulses: The number of pulses the stage(s) should move.

        !!! example
            * `move_relative(1, 1000)` &mdash; move stage 1 by 1000 pulses in the `+` direction
            * `move_relative(2, -5000)` &mdash; move stage 2 by 5000 pulses in the `-` direction
            * `move_relative('W', 1000, -5000)` &mdash; move stage 1 by 1000 pulses in the `+` direction, and
                move stage 2 by 5000 pulses in the `-` direction
        """
        self._move("M", stage, *num_pulses)

    def set_mode(self, stage: Literal[1, 2, "W"], mode: Literal[0, 1] | Mode) -> None:
        """Set whether the stage(s) can be moved by hand or by the motor.

        Args:
            stage: The stage(s) to set the mode of.

                * `1` &mdash; set the mode for stage 1
                * `2` &mdash; set the mode for stage 2
                * `"W"` &mdash; set the mode for stages 1 and 2

            mode: Whether the stage(s) can be moved by hand (0) or by motor (1).
        """
        reply = self.query(f"C:{stage}{mode}")
        if not reply.startswith("OK"):
            msg = f"Cannot set stage {stage} to mode={mode}"
            raise MSLConnectionError(self, msg)

    def set_origin(self, stage: Literal[1, 2, "W"]) -> None:
        """Set the origin of the stage(s) to its current position.

        Args:
            stage: The stage(s) to set the home of.

                * `1` &mdash; set the home for stage 1
                * `2` &mdash; set the home for stage 2
                * `"W"` &mdash; set the home for stages 1 and 2
        """
        reply = self.query(f"R:{stage}")
        if not reply.startswith("OK"):
            msg = f"Cannot set the origin for stage {stage}"
            raise MSLConnectionError(self, msg)

    def set_output_status(self, status: Literal[0, 1]) -> None:
        """Set the I/O output status.

        Args:
            status: Can either be 0 or 1 (see manual).
        """
        reply = self.query(f"O:{status}")
        if not reply.startswith("OK"):
            msg = f"Cannot set the output status to {status}"
            raise MSLConnectionError(self, msg)

    def set_speed(self, stage: Literal[1, 2, "W"], *speeds: Speed) -> None:
        """Set the speed when moving to a position.

        Args:
            stage: The stage(s) to set the speed settings for.

                * `1` &mdash; set the speed for stage 1
                * `2` &mdash; set the speed for stage 2
                * `"W"` &mdash; set the speed for stages 1 and 2
                    (`speeds` is then the speed settings for stage 1, stage 2)

            speeds: The speed settings.

        !!! example
            * `set_speed(1, Speed(100, 1000, 50))` &mdash; stage 1 moves at a minimum speed of 100 PPS,
                maximum speed of 1000 PPS and a 50 ms acceleration/deceleration time.
            * `set_speed("W", Speed(100, 1000, 50), Speed(200, 2000, 100))` &mdash; stage 1 moves at a
                minimum speed of 100 PPS, maximum speed of 1000 PPS and a 50 ms acceleration/deceleration time, and,
                stage 2 moves at a minimum speed of 200 PPS, maximum speed of 2000 PPS and a 100 ms
                acceleration/deceleration time.
        """
        self._speed("D", stage, *speeds)

    def set_speed_origin(self, stage: Literal[1, 2, "W"], *speeds: Speed) -> None:
        """Set the speed when moving to the origin.

        Args:
            stage: The stage(s) to set the speed settings for.

                * `1` &mdash; set the speed for stage 1
                * `2` &mdash; set the speed for stage 2
                * `"W"` &mdash; set the speed for stages 1 and 2
                    (`speeds` is then the speed settings for stage 1, stage 2)

            speeds: The speed settings.

        !!! example
            * `set_speed_origin(2, Speed(100, 1000, 50))` &mdash; stage 2 moves at a minimum speed of 100 PPS,
                maximum speed of 1000 PPS and a 50 ms acceleration/deceleration time.
            * `set_speed_origin("W", Speed(100, 1000, 50), Speed(200, 2000, 100))` &mdash; stage 1 moves at a
                minimum speed of 100 PPS, maximum speed of 1000 PPS and a 50 ms acceleration/deceleration time, and,
                stage 2 moves at a minimum speed of 200 PPS, maximum speed of 2000 PPS and a 100 ms
                acceleration/deceleration time.
        """
        self._speed("V", stage, *speeds)

    def set_steps(self, stage: Literal[1, 2], steps: int) -> None:
        """Set the number of steps that the stage motor will use.

        See the manual for more details (the `S` command).

        Args:
            stage: The stage to set the steps of.
            steps: The number of steps that the motor should use (must be one of
                `1`, `2`, `4`, `5`, `8`, `10`, `20`, `25`, `40`, `50`, `80`, `100`, `125`, `200`, `250`).
        """
        reply = self.query(f"S:{stage}{steps}")
        if not reply.startswith("OK"):
            msg = f"Cannot set stage {stage} to #steps={steps}"
            raise MSLConnectionError(self, msg)

    def status(self) -> Status:
        """Get the current position and state of each stage.

        Returns:
            The current position and state of each stage.
        """
        reply = self.query("Q:")
        if reply == "NG":  # then try again
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            return self.status()

        match = self._status_regex.match(reply)
        if not match:
            msg = f"Invalid regex expression for the reply {reply!r}"
            raise MSLConnectionError(self, msg)

        negative1, position1, negative2, position2, ok, state, moving = match.groups()
        if ok != "K":
            msg = f"Controller indicates a command or parameter error, reply={reply!r}"
            raise MSLConnectionError(self, msg)

        pos1 = -int(position1) if negative1 else int(position1)
        pos2 = -int(position2) if negative2 else int(position2)
        return Status(pos1, pos2, State(state), moving == "B")

    def stop(self) -> None:
        """Immediately stop both stages from moving."""
        reply = self.query("L:E")
        if not reply.startswith("OK"):
            msg = "Cannot stop the stages"
            raise MSLConnectionError(self, msg)

    def stop_slowly(self, stage: Literal[1, 2, "W"]) -> None:
        """Slowly bring the stage(s) to a stop.

        Args:
            stage: The stage(s) to slowly stop.

                * `1` &mdash; slowly stop stage 1
                * `2` &mdash; slowly stop stage 2
                * `"W"` &mdash; slowly stop stages 1 and 2
        """
        reply = self.query(f"L:{stage}")
        if not reply.startswith("OK"):
            msg = f"cannot slowly stop stage {stage}"
            raise MSLConnectionError(self, msg)

    def wait(self, callback: Callable[[Status], None] | None = None, sleep: float = 0.05) -> None:
        """Wait for all stages to finish moving.

        This is a blocking call because it uses [sleep][time.sleep].

        Args:
            callback: A callable function. The function will receive 1 argument,
                the [Status][msl.equipment_resources.optosigma.shot702.Status]
            sleep: The number of seconds to wait between calls to the `callback`.
        """
        while True:
            status = self.status()
            if callback is not None:
                callback(status)
            if not status.is_moving:
                return
            time.sleep(sleep)

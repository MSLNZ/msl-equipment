"""Establishes a connection to a TC Series Temperature Controller from Electron Dynamics Ltd.

The main communication class is [TCSeries][msl.equipment_resources.electron_dynamics.tc_series.TCSeries].
"""

# cSpell: ignore ADCR
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import TYPE_CHECKING

from msl.equipment.interfaces import MSLConnectionError, Serial
from msl.equipment.utils import to_enum

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class AlarmType(IntEnum):
    """Alarm type.

    Attributes:
        OFF (int): 0
        MIN (int): 1
        MAX (int): 2
        BOTH (int): 3
    """

    OFF = 0
    MIN = 1
    MAX = 2
    BOTH = 3


class ControlType(IntEnum):
    """Control type.

    Attributes:
        ON_OFF (int): Output drive is only fully on (heating or cooling) or off, `1`.
        P (int): Proportional, `2`.
        PI (int): Proportional and integral, `3`.
        PID (int): Proportional, integral and derivative, `4`.
    """

    ON_OFF = 1
    P = 2
    PI = 3
    PID = 4


class Method(IntEnum):
    """Setpoint method type.

    The temperature setpoint can be set via software or by altering the potentiometer
    on the temperature controller hardware.

    Attributes:
        POTENTIOMETER (int): 0
        SOFTWARE (int): 1
        INPUT (int): 2
    """

    POTENTIOMETER = 0
    SOFTWARE = 1
    INPUT = 2


class Polarity(IntEnum):
    """Output drive polarity.

    Attributes:
        NEGATIVE (int): 0
        POSITIVE (int): 1
    """

    NEGATIVE = 0
    POSITIVE = 1


class PowerUpState(IntEnum):
    """Temperature control state from power up.

    Attributes:
        OFF (int): 0
        ON (int): 1
        LAST (int): 2 (same as the last setting prior to power off)
    """

    OFF = 0
    ON = 1
    LAST = 2


class SensorType(IntEnum):
    """Sensor type.

    Attributes:
        VOLTAGE (int): 0
        PT100 (int): 1
        LM35 (int): 2
        LM50 (int): 3
        LM60 (int): 4
        LM61 (int): 5
        NTC_THERMISTOR (int): 6
        RES (int): 7
        PT1000 (int): 8
        RTD (int): 9
    """

    VOLTAGE = 0
    PT100 = 1
    LM35 = 2
    LM50 = 3
    LM60 = 4
    LM61 = 5
    NTC_THERMISTOR = 6
    RES = 7
    PT1000 = 8
    RTD = 9


class Unit(Enum):
    """The temperature unit.

    Attributes:
        C (str): Celsius, `"C"`.
        F (str): Fahrenheit, `"F"`.
        K (str): Kelvin, `"K"`.
        V (str): Voltage, `"V"`.
        R (str): Resistance, `"R"`.
    """

    C = "C"
    F = "F"
    K = "K"
    V = "V"
    R = "R"


@dataclass
class Alarm:
    """Alarm parameters.

    Args:
        alarm_min: The temperature below which the alarm is activated.
        alarm_max: The temperature above which the alarm is activated.
        ok_min: The minimum temperature difference from the setpoint for the temperature to be okay.
        ok_max: The maximum temperature difference from the setpoint for the temperature to be okay.
        limit_min: The minimum temperature below which the drive output is disabled.
        limit_max: The maximum temperature above which the drive output is disabled.
    """

    type: AlarmType
    alarm_min: float
    alarm_max: float
    ok_min: float
    ok_max: float
    limit_min: float
    limit_max: float


@dataclass
class Control:
    """The PID control parameters.

    Args:
        type: The control type.
        p: The proportional (gain) value. With a proportional control type, the controller output is
            proportional to the temperature error from the setpoint. The proportional terms sets
            the gain for this, i.e., `Output = setpoint-actual-temperature * proportional-term`
        i: The integral value. With integral action, the controller output is proportional to the
            amount of time the error is present. Integral action eliminates offset. The integral term
            is a time unit in seconds. NB for larger effects of integration reduce the integral time,
            also for operation without integral, integral time can be set to a large number, e.g. 1e6.
        d: The derivative value. With derivative action, the controller output is proportional to
            the rate of change of the measurement or error. The controller output is calculated by
            the rate of change of the measurement with time, in seconds. To increase the derivative
            action increase the derivative value.
        d_filter: The derivative filter is a low pass filter function on the derivative value.
            This allows the filtration of noise components which are a problem with a pure
            derivative function. The filter value should be set to be between 0 and 1.
        dead_band: For use with On/Off control the dead band specifies the temperature range
            around the set point where the output is zero. For example:

            * Temperature > setpoint + dead_band (Fully Cooling)
            * Temperature < setpoint - dead_band (Fully Heating)
            * Temperature < setpoint + dead_band AND > setpoint-dead_band (Output off)

        power_up_state: Temperature control state from power up.
    """

    type: ControlType
    p: float
    i: float
    d: float
    d_filter: float
    dead_band: float
    power_up_state: PowerUpState


@dataclass(init=False)
class Output:
    """Output parameters."""

    def __init__(self, polarity: int | Polarity, minimum: float, maximum: float, frequency: float) -> None:
        """Output parameters.

        Args:
            polarity: Output drive polarity.
            minimum: The minimum value limit of the output. Range -100 to +100.
            maximum: The maximum value limit of the output. Range -100 to +100.
            frequency: Sets the pulse-width modulation repetition frequency of the output drive.
                Range 20 to 1000 Hz.
        """
        if abs(minimum) > 100:  # noqa: PLR2004
            msg = f"Invalid minimum={minimum}. Must be between -100 and +100"
            raise ValueError(msg)
        if abs(maximum) > 100:  # noqa: PLR2004
            msg = f"Invalid maximum={maximum}. Must be between -100 and +100"
            raise ValueError(msg)
        if minimum > maximum:
            msg = f"The minimum={minimum} value must be less than the maximum={maximum}"
            raise ValueError(msg)
        if frequency < 20 or frequency > 1000:  # noqa: PLR2004
            msg = f"Invalid frequency={frequency}. Must be between 20 and 1000"
            raise ValueError(msg)

        self.polarity: Polarity = to_enum(polarity, Polarity)
        self.minimum: float = minimum
        self.maximum: float = maximum
        self.frequency: float = frequency


@dataclass
class Sensor:
    r"""Sensor parameters.

    Args:
        type: Sensor type.
        x2: See `c` description.
        x: See `c` description.
        c: The `x2`, `x` and `c` parameters are the quadratic, linear and constant coefficients that
            are used to convert the sensor voltage into a temperature, i.e.,
            `temperature = (v * v * x2) + (v * x) + c`, where `v` is the measured sensor voltage.
            For *NTC thermistors*, `x2` is the beta value as specified for the thermistor type,
            `x` is the resistance at $25~^\circ\text{C}$, and `c` is still the offset.
        unit: The temperature unit.
        averaging: Whether to enable or disable averaging.
        r: Used for *NTC* or *RES* sensors and corresponds to the RL drive resistance.
    """

    type: SensorType
    x2: float
    x: float
    c: float
    unit: Unit
    averaging: bool
    r: float = 22000.0


@dataclass
class Setpoint:
    """The setpoint parameters.

    Args:
        method: The setpoint method.
        value: The setpoint value.
        pot_range: The temperature range of the potentiometer.
        pot_offset: The minimum temperature value of the potentiometer.
    """

    method: Method
    value: float
    pot_range: float
    pot_offset: float


@dataclass
class Status:
    """Controller status.

    Args:
        setpoint: Setpoint value.
        temperature: The measured temperature (for the specified
            [Sensor][msl.equipment_resources.electron_dynamics.tc_series.Sensor]
            [Unit][msl.equipment_resources.electron_dynamics.tc_series.Unit]).
        controlled: Whether the temperature control drive is on or off.
        output: The output value (between -100 and 100).
        alarm_type: The type of alarm used.
        faults: Fault flags.

            * bit 0: ADC fault.
            * bit 1: ADCR fault.
            * bit 2: VDC limit.
            * bit 3: Temperature limit.
            * bit 4: Inhibited.

        temp_ok: Whether the temperature is ok (within range).
        supply_v: The supply voltage.
        version: The firmware version number of the controller.
        test_cycles: The number of test cycles that have occurred.
        test_mode_completed: Whether the test has completed.
    """

    setpoint: float
    temperature: float
    controlled: bool
    output: float
    alarm_type: AlarmType
    faults: int
    temp_ok: bool
    supply_v: float
    version: str
    test_cycles: float
    test_mode_completed: bool


class TCSeries(Serial, manufacturer=r"Electron Dynamics", model=r"TC\s*[M|L]", flags=re.IGNORECASE):
    """Establishes a connection to a TC Series Temperature Controller from Electron Dynamics Ltd."""

    def __init__(self, equipment: Equipment) -> None:
        """Establishes a connection to a TC Series Temperature Controller from Electron Dynamics Ltd.

        Args:
            equipment: An [Equipment][] instance.
        """
        assert equipment.connection is not None  # noqa: S101
        if not equipment.connection.properties:
            # then use the default connection properties
            equipment.connection.properties = {
                "baud_rate": 19200,
                "write_termination": None,
                "read_termination": "\r\n",
                "timeout": 10.0,
            }
        super().__init__(equipment)

    @staticmethod
    def _checksum(msg: str) -> int:
        return (sum(map(ord, msg)) + 1) & 0xFF

    def _send(self, command: str, data: str) -> None:
        msg = f"{command}{len(data):02d}{data}"
        _ = self.write(f"\01{msg}{self._checksum(msg):02X}")

    def _reply(self, command: str) -> list[str]:
        self._send(command, "")
        reply = self.read()
        checksum = self._checksum(reply[1:-2])
        if int(reply[-2:], 16) != checksum:
            msg = f"Checksum mismatch. Got {reply[-2:]!r}, expect '{checksum:02X}'"
            raise MSLConnectionError(self, msg)
        return reply[4:-3].split(";")

    def get_alarm(self) -> Alarm:
        """Get the alarm parameters.

        Returns:
            The alarm parameters.
        """
        a, b, c, d, e, f, g = map(float, self._reply("d"))
        return Alarm(
            type=AlarmType(int(a)),
            alarm_min=b,
            alarm_max=c,
            ok_min=d,
            ok_max=e,
            limit_min=f,
            limit_max=g,
        )

    def get_control(self) -> Control:
        """Get the PID control parameters.

        Returns:
            The control parameters.
        """
        a, b, c, d, e, f, g = map(float, self._reply("b"))
        return Control(
            type=ControlType(int(a)),
            p=b,
            i=c,
            d=d,
            d_filter=e,
            dead_band=f,
            power_up_state=PowerUpState(int(g)),
        )

    def get_output(self) -> Output:
        """Get the output parameters.

        Returns:
            The output parameters.
        """
        a, b, c, d = map(float, self._reply("h"))
        return Output(
            polarity=Polarity(int(a)),
            minimum=b,
            maximum=c,
            frequency=d,
        )

    def get_sensor(self) -> Sensor:
        """Get the sensor parameters.

        Returns:
            The sensor parameters.
        """
        data = list(map(float, self._reply("f")))
        return Sensor(
            type=SensorType(int(data[0])),
            x2=data[1],
            x=data[2],
            c=data[3],
            unit=Unit(data[4]),
            averaging=data[5] == 1,
            r=0.0 if len(data) < 7 else data[6],  # noqa: PLR2004
        )

    def get_setpoint(self) -> Setpoint:
        """Get the setpoint parameters.

        Returns:
            The setpoint parameters.
        """
        a, b, c, d = map(float, self._reply("q"))
        return Setpoint(
            method=Method(int(a)),
            value=b,
            pot_range=c,
            pot_offset=d,
        )

    def get_status(self) -> Status:
        """Get the status.

        Returns:
            The status parameters.
        """
        r = self._reply("j")
        return Status(
            setpoint=float(r[0]),
            temperature=float(r[1]),
            controlled=r[2] == "1",
            output=float(r[3]),
            alarm_type=AlarmType(int(r[4])),
            faults=int(r[5]),
            temp_ok=r[6] == "1",
            supply_v=float(r[7]),
            version=r[8],
            test_cycles=int(r[9]),
            test_mode_completed=r[10] == "1",
        )

    def set_alarm(self, alarm: Alarm) -> None:
        """Set the alarm parameters.

        Args:
            alarm: The alarm parameters.
        """
        data = (
            f"{alarm.type};{alarm.alarm_min:.3f};{alarm.alarm_max:.3f};{alarm.ok_min:.3f};"
            f"{alarm.ok_max:.3f};{alarm.limit_min:.3f};{alarm.limit_max:.3f};"
        )
        self._send("c", data)

    def set_control(self, control: Control) -> None:
        """Set the PID control parameters.

        Args:
            control: The control parameters.
        """
        data = (
            f"{control.type};{control.p:.3f};{control.i:.3f};{control.d:.3f};"
            f"{control.d_filter:.3f};{control.dead_band:.3f};{control.power_up_state};"
        )
        self._send("a", data)

    def set_output(self, output: Output) -> None:
        """Set the output parameters.

        Args:
            output: The output parameters.
        """
        data = f"{output.polarity};{output.minimum:.3f};{output.maximum:.3f};{output.frequency:.3f};"
        self._send("g", data)

    def set_output_drive(self, *, enable: bool, value: float) -> None:
        """Set the output drive state and value.

        Args:
            enable: Whether to enable or disable the output drive.
            value: Percent drive output.
        """
        self._send("m", f"{int(enable)};{value:.3f};")

    def set_sensor(self, sensor: Sensor) -> None:
        """Set the sensor type and the sensor parameters.

        Args:
            sensor: The sensor parameters.
        """
        data = f"{sensor.type};{sensor.x2:.3f};{sensor.x:.3f};{sensor.c:.3f};{sensor.unit};{int(sensor.averaging)};"
        if sensor.type in (SensorType.NTC_THERMISTOR, SensorType.RES):
            data += f"{sensor.r:.3f};"
        self._send("e", data)

    def set_setpoint(self, setpoint: Setpoint) -> None:
        """Set the setpoint parameters.

        Args:
            setpoint: The setpoint parameters.
        """
        data = f"{setpoint.method};{setpoint.value:.3f};{setpoint.pot_range:.3f};{setpoint.pot_offset:.3f};"
        self._send("i", data)

    def set_test(self, mode: int, *data: float) -> None:
        """Set the test parameters.

        Args:
            mode: The test mode. One of:

                * `0`: Off
                * `1`: Normal
                * `2`: Temperature cycle
                * `3`: Temperature ramp
                * `4`: Auto tune

            data: The test data.
        """
        if mode < 0 or mode > 4:  # noqa: PLR2004
            msg = f"Invalid test mode={mode}. Must be 0, 1, 2, 3 or 4"
            raise ValueError(msg)

        values = ";".join(f"{v:.3f}" for v in data)
        self._send("k", f"{mode};{values};")

"""[Vaisala](https://www.vaisala.com/en){:target="_blank"} PTU300 series barometer.

Supports models PTU300, PTU301, PTU303, PTU307 and PTU30T.
"""

# cSpell: ignore baro psia barg psig
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from msl.equipment.enumerations import DataBits, Parity
from msl.equipment.interfaces import MSLConnectionError, Serial

if TYPE_CHECKING:
    from msl.equipment.schema import Equipment


class PTU300(Serial, manufacturer=r"Vaisala", model=r"^PTU30[0137T]$", flags=re.IGNORECASE):
    """[Vaisala](https://www.vaisala.com/en){:target="_blank"} PTU300 series barometer."""

    def __init__(self, equipment: Equipment) -> None:
        """Vaisala PTU300 series barometer.

        The device manual is available [here](https://docs.vaisala.com/v/u/M210796EN-J/en-US){:target="_blank"}.

        The default settings for the RS232 connection are:

        * Baud rate: 4800
        * Data bits: 7
        * Parity: EVEN

        !!! warning
            Ensure the device is in `STOP` or `SEND` mode before initiating communication.

        Args:
            equipment: An [Equipment][] instance.
        """
        assert equipment.connection is not None  # noqa: S101
        equipment.connection.properties.setdefault("baud_rate", 4800)
        equipment.connection.properties.setdefault("data_bits", DataBits.SEVEN)
        equipment.connection.properties.setdefault("parity", Parity.EVEN)
        super().__init__(equipment)

        self.rstrip: bool = True

        self._units: dict[str, str] = {}
        self._pressure_modules: set[str] = set()
        self._info: dict[str, str] = self._device_info()

        # Get the device ID (serial) number and check it agrees with the equipment record.
        # Could use `reply = self.query("*9900SN")` but the serial number is also in device_info
        sn = self._info["Serial number"]
        if sn != equipment.serial:
            msg = f"Inconsistent serial number: expected {equipment.serial} but received {sn}"
            raise MSLConnectionError(self, msg)

    def _device_info(self) -> dict[str, str]:
        """Returns a dictionary of information about the Vaisala device."""
        info: dict[str, str] = {}
        break_keys = {
            "PTU30": "module 2",
            "PTB33": "module 4",
        }
        break_key = "TBC"
        _ = self.write("?")
        while True:
            ok = self.read()
            try:
                key, val = ok.split(": ")
                info[key.strip()] = val.strip()
                if "baro" in val.lower():
                    self._pressure_modules.add(val)
                if break_key in key.lower():
                    break
            except ValueError:
                model, version = ok.split(" / ")
                info["Model"] = model
                break_key = break_keys[model[:-1]]
                info["Version"] = version

        return info

    def check_for_errors(self) -> None:
        """Raise an error, if present."""
        err = self.query("ERRS")  # List present transmitter errors
        # a PASS or FAIL line is returned from PTB330 modules first
        if err in {"PASS", "FAIL"}:
            err = self.read()
        if err and err != "No errors":
            raise MSLConnectionError(self, err)

    @property
    def device_info(self) -> dict[str, str]:
        """Returns a dictionary of information about the Vaisala device."""
        return self._info

    def get_format(self) -> str:
        """Get the currently active formatter string.

        Returns:
            The formatter string.
        """
        # The hash symbol "#" is used to set the format, but then appears as a backslash "\\" on the device.
        return self.query("FORM ?")[len("Output format  :") :].replace("\\", "#")

    def get_reading_str(self) -> str:
        """Output the reading once.

        Returns:
            A string that follows the format set by
                [set_format][msl.equipment_resources.vaisala.ptu300.PTU300.set_format].
        """
        return self.query("SEND")

    def set_format(self, fmt: str) -> None:
        """Set the format of data output to follow the pattern in the format string.

        For example, in the format string `4.3 P " " 3.3 T " " 3.3 RH " " SN " " #r #n`, `x.y` is the number
        of digits and decimal places of the values; `P`, `T`, `RH`, and `SN` are placeholders for pressure,
        temperature, relative humidity, and serial number values; and `" "`, `#r`, and `#n` represent a string
        constant, carriage-return, and line-feed respectively. Additional allowed modifiers include `ERR` for
        error flags, `U5` for unit field and (optional) length, `TIME` for time as [hh:mm:ss], and `DATE` for
        date as [yyyy-mm-dd]. For more options, refer to the manual.

        Args:
            fmt: String representing desired output format.
        """
        reply = self.query(f"FORM {fmt}")
        if reply.startswith("Output format  :"):  # format is returned by some devices when set
            form = reply[len("Output format  :") :].replace("\\", "#")
        elif "ok" in reply.lower():  # if OK is returned then we need to ask for the format
            form = self.get_format()
        else:  # this is not expected so raise an error
            msg = f"Unexpected reply={reply!r}"
            raise MSLConnectionError(self, msg)

        if form.upper().replace(" ", "") != fmt.upper().replace(" ", ""):
            # the format was not set as specified
            self.check_for_errors()
            msg = f"Could not set format of output. \nExpected: {fmt} \nReceived: {form}."
            raise MSLConnectionError(self, msg)

        self._info["Output format"] = form

    def set_units(self, desired_units: dict[str, str]) -> None:  # noqa: C901, PLR0912
        """Set unit of specified quantity.

        Note that only one pressure unit is used at a time for the PTU300 series.

        Args:
            desired_units: Dictionary of *quantity* (as keys) and their *unit* (as values)
                as specified in the instrument manual on pages 24 and 106.

                These may include the following (available options depend on the barometer components):

                * Pressure *quantity*: P, P3h, P1, P2, QNH, QFE, HCP, ...
                * Pressure *unit*: hPa, psi, inHg, torr, bar, mbar, mmHg, kPa, Pa, mmH2O, inH2O
                * Temperature *quantity*: T
                * Temperature *unit*: 'C, 'F (C and F are also supported but are returned as 'C or 'F)
                * Humidity *quantity*: RH
                * Humidity *unit*: %RH
        """
        p_units: list[str] = []
        allowed_units = [  # for pressure
            "hPa",
            "psia",
            "inHg",
            "torr",
            "bara",
            "barg",
            "psig",
            "mbar",
            "mmHg",
            "kPa",
            "Pa",
            "mmH2O",
            "inH2O",
        ]
        old_units = self.query("UNIT")
        if "Output units" not in old_units:  # confirming device is of type PTU300
            msg = "Check correct device connected"
            raise MSLConnectionError(self, msg)

        for quantity, unit in desired_units.items():
            if quantity == "RH":  # only option is %RH
                self._units["RH"] = "%RH"

            elif "T" in quantity:  # options are 'C, 'F
                if "F" in unit:  # Temperature and humidity setting is done via metric or 'non metric'
                    r_m = self.query("UNIT N")
                    if "non" not in r_m:
                        msg = "Error when setting non-metric unit for temperature"
                        raise MSLConnectionError(self, msg)
                    self._units["T"] = "'F"
                elif "C" in unit:
                    r_m = self.query("UNIT M")
                    self._units["T"] = "'C"
                else:
                    msg = f"Unit {unit} is not supported by this device. Please use 'C or 'F."
                    raise MSLConnectionError(self, msg)

                if "metric" not in r_m:
                    self._units["T"] = ""
                    self.check_for_errors()

            elif unit in allowed_units:  # assume this is a pressure quantity based on the unit
                if p_units and unit not in p_units:
                    msg = "Only one pressure unit can be set for this barometer"
                    raise MSLConnectionError(self, msg)

                r_p = self.query(f"UNIT P {unit}")
                if not r_p.endswith(unit):
                    self.check_for_errors()
                self._units[quantity] = unit
                p_units.append(unit)

            else:  # quantity is not pressure, temperature or humidity, so ask user to set the unit manually
                msg = f"{unit} is not able to be set for {quantity}. Please set this unit manually."
                raise MSLConnectionError(self, msg)

    @property
    def units(self) -> dict[str, str]:
        """A dictionary of measured quantities and their associated units.

        The units are set by [set_units][msl.equipment_resources.vaisala.ptu300.PTU300.set_units].
        """
        return self._units

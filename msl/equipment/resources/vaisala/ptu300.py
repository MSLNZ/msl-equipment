"""
Vaisala PTU300 series barometer which reads temperature, relative humidity, and pressure.
Supports models PTU300, PTU301, PTU303, PTU307 and PTU30T.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from msl.equipment import EquipmentRecord
from msl.equipment.resources import register
from msl.equipment.exceptions import VaisalaError
from msl.equipment.connection_serial import ConnectionSerial

from msl.equipment.constants import (
    Parity,
    DataBits,
)


@register(manufacturer=r'Vaisala', model=r'^PTU30[0137T]$', flags=re.IGNORECASE)
class PTU300(ConnectionSerial):

    def __init__(self, record: EquipmentRecord) -> None:
        """Vaisala Barometer PTU300 series (models PTU300, PTU301, PTU303, PTU307 and PTU30T).
        The device manual is available `here <https://docs.vaisala.com/v/u/M210796EN-J/en-US>`_.

        .. note::
            Ensure the device is in STOP or SEND mode before initiating a connection to a PC.

        The default settings for the RS232 connection are:

        * Baud rate = 4800
        * Data bits = 7
        * Stop bits = 1
        * Parity = EVEN
        * Flow control = None

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        props = record.connection.properties
        props.setdefault('baud_rate', 4800)
        props.setdefault('data_bits', DataBits.SEVEN)
        props.setdefault('parity', Parity.EVEN)
        super(PTU300, self).__init__(record)

        self.set_exception_class(VaisalaError)
        self.rstrip = True

        self._units = {}
        self._pressure_modules = set()
        self._info = self._device_info()

        # Get the device ID (serial) number and check it agrees with the equipment record.
        # can use reply = self.query("*9900SN") but the serial number is also in device_info
        sn = self._info["Serial number"]
        if not sn == record.serial:
            self.raise_exception(f"Inconsistent serial number: expected {record.serial} but received {sn}")

    def _device_info(self) -> dict[str, str]:
        """Return a dictionary of information about the Vaisala device.
        """
        info = {}
        break_keys = {
            'PTU30': "module 2",
            'PTB33': "module 4",
        }
        break_key = "TBC"
        self.write("?")
        while True:
            ok = self.read()
            try:
                key, val = ok.split(': ')
                info[key.strip()] = val.strip()
                if 'baro' in val.lower():
                    self._pressure_modules.add(val)
                if break_key in key.lower():
                    break
            except ValueError:
                model, version = ok.split(" / ")
                info['Model'] = model
                break_key = break_keys[model[:-1]]
                info['Version'] = version

        return info

    @property
    def device_info(self) -> dict[str, str]:
        """Return a dictionary of information about the Vaisala device.
        """
        return self._info

    def set_units(self, desired_units: dict[str, str]) -> None:
        """Set units of specified quantities. Note that only one pressure unit is used at a time for the PTU300 series.

        :param desired_units: Dictionary of quantities (as keys) and their unit (their value)
            as specified in the instrument manual on pages 22 and 106.

            These may include the following (available options depend on the barometer components):

              * Pressure quantities: P, P3h, P1, P2, QNH, QFE, HCP, ...
              * Pressure units: hPa, psi, inHg, torr, bar, mbar, mmHg, kPa, Pa, mmH2O, inH2O
              * Temperature quantity: T
              * Temperature units: 'C, 'F (C and F are also supported but are returned as 'C or 'F)
              * Humidity quantity: RH
              * Humidity unit: %RH
        """
        p_units = []
        allowed_units = [        # for pressure
            'hPa', 'psia', 'inHg', 'torr', 'bara', 'barg', 'psig', 'mbar', 'mmHg', 'kPa', 'Pa', 'mmH2O', 'inH2O'
        ]
        old_units = self.query("UNIT")
        if not "Output units" in old_units:  # confirming device is of type PTU300
            self.raise_exception("Check correct device connected")

        for quantity, u in desired_units.items():
            if quantity == "RH":    # only option is %RH
                self._units["RH"] = "%RH"

            elif "T" in quantity:   # options are 'C, 'F
                if "F" in u:        # Temperature and humidity setting is done via metric or 'non metric'
                    r_m = self.query("UNIT N")
                    if not 'non' in r_m:
                        self.raise_exception("Error when setting non metric units")
                    self._units["T"] = "'F"
                elif "C" in u:
                    r_m = self.query("UNIT M")
                    self._units["T"] = "'C"
                else:
                    self.raise_exception(f"Unit {u} is not supported by this device. Please use 'C or 'F.")

                if not 'metric' in r_m:
                    self._units["T"] = None
                    self.check_for_errors()

            elif u in allowed_units:  # assume this is a pressure quantity based on the unit
                if p_units and u not in p_units:
                    self.raise_exception("Only one pressure unit can be set for this barometer")
                r_p = self.query(f"UNIT P {u}")
                if not r_p.endswith(u):
                    self.check_for_errors()
                self._units[quantity] = u
                p_units.append(u)

            else:  # quantity is not pressure, temperature or humidity, so ask user to set the unit manually
                self.raise_exception(f"{u} is not able to be set for {quantity}. Please set this unit manually.")

    @property
    def units(self) -> dict[str, str]:
        """A dictionary of measured quantities and their associated units as set on the device by :meth:`.set_units`."""
        return self._units

    def set_format(self, fmt: str) -> None:
        """Set the format of data output to follow the pattern in the format string.  For example, in the format string
        ``4.3 P " " 3.3 T " " 3.3 RH " " SN " " #r #n``, x.y is the number of digits and decimal places of the values;
        P, T, RH, and SN are placeholders for pressure, temperature, relative humidity, and serial number values;
        and " ", #r, and #n represent a string constant, carriage-return, and line feed respectively.
        Additional allowed modifiers include ERR for error flags, U5 for unit field and (optional) length,
        TIME for time as [hh:mm:ss], and DATE for date as [yyyy-mm-dd]. For more options, refer to the manual.

        :param fmt: string representing desired output format
        """
        ok = self.query(f'FORM {fmt}')
        if ok.startswith('Output format  :'):    # format is returned by some devices when set
            form = ok.lstrip('Output format  :').replace("\\", "#")
        elif "ok" in ok.lower():        # if OK is returned then we need to ask for the format
            form = self.get_format()
        else:                           # this is not expected so raise an error
            self.raise_exception(ok)

        if not form.upper().replace(" ", "") == fmt.upper().replace(" ", ""):
            # the format was not set as specified
            self.check_for_errors()
            self.raise_exception(f"Could not set format of output. \nExpected: {fmt} \nReceived: {form}.")

        self._info['Output format'] = form

    def get_format(self) -> str:
        r"""Return the currently active formatter string.
        The hash symbol "#" is used to set the format, but then appears as a backslash "\\" on the device.
        """
        return self.query("FORM ?").lstrip('Output format  :').replace("\\", "#")

    def get_reading_str(self) -> str:
        """Output the reading once. The returned string follows the format set by :meth:`.set_format`."""
        return self.query("SEND")

    def check_for_errors(self) -> None:
        """Raise an error if present."""
        err = self.query("ERRS")  # List present transmitter errors
        # a PASS or FAIL line is returned from PTB330 modules first
        if err == "PASS":
            err = self.read()
        elif err == "FAIL":
            err = self.read()
        if err and not err == 'No errors':
            self.raise_exception(err)

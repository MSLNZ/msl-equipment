"""
Vaisala Barometer which reads temperature, relative humidity, and pressure, e.g. of type PTU300
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from msl.equipment import EquipmentRecord
from msl.equipment.resources import register
from msl.equipment.exceptions import VaisalaError
from msl.equipment.connection_serial import ConnectionSerial


@register(manufacturer=r'Vaisala', model=r'PTU30*', flags=re.IGNORECASE)
class PTU300(ConnectionSerial):

    def __init__(self, record: EquipmentRecord) -> None:
        """Vaisala Barometer PTU300 series.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        :param record: A record from an :ref:`equipment-database`.
        """
        super(PTU300, self).__init__(record)

        self.set_exception_class(VaisalaError)
        self.rstrip = True

        self.ID = record.serial

        self.stop_run_mode()

        self.pressure_modules = set()
        self.info = self.device_info(show=False)
        self.check_serial()

        self._units = {}

    def check_serial(self) -> str:
        """Get the device ID (serial) number and check it agrees with the equipment record.
        """
        # can use reply = self.query("*9900SN") but the serial number is also in the device info
        sn = self.info["Serial number"]
        if not sn == self.ID:
            self.raise_exception(f"Inconsistent serial number: expected {self.ID} but received {sn}")
        return sn

    def device_info(self, show: bool = True) -> dict:
        """Prints information about the Vaisala device
        """
        info = {}
        break_keys = {  # TODO need a proper regex here to make sure all devices are covered
            'PTU300': "module 2",
            'PTB330': "module 4",
        }
        break_key = "TBC"
        self.write("?")
        while True:
            ok = self.read()
            if show:
                print(ok)
            try:
                key, val = ok.split(': ')
                info[key.strip()] = val.strip()
                if 'baro' in val.lower():
                    self.pressure_modules.add(val)
                if break_key in key.lower():
                    break
            except ValueError:
                model, version = ok.split(" / ")
                info['Model'] = model
                break_key = break_keys[model]
                info['Version'] = version

        return info

    def set_units(self, *, celcius: bool = True, p_unit: tuple[str, str] = ('P', 'hPa')) -> None:
        """Set units to be metric or non-metric, and/or set the desired pressure unit

        :param celcius: True for metric units (ºC), or False for non-metric (ºF)
        :param p_unit: a tuple of the pressure quantity (here P), and a unit from
            ['hPa', 'psia', 'inHg', 'torr', 'bara', 'barg', 'psig', 'mbar', 'mmHg', 'kPa', 'Pa', 'mmH2O', 'inH2O']
        :return:
        """
        # Pressure
        allowed_units = [
            'hPa', 'psia', 'inHg', 'torr', 'bara', 'barg', 'psig', 'mbar', 'mmHg', 'kPa', 'Pa', 'mmH2O', 'inH2O'
        ]
        check_string_m = "Output units   : metric"
        available_units = self.query("UNIT")
        if available_units == check_string_m:  # device is of type PTU300
            # Temperature and humidity: metric or 'non metric'
            if celcius:
                r_m = self.query("UNIT M")
                self._units["T"] = "ºC"
            else:
                r_m = self.query("UNIT N")
                self._units["T"] = "ºF"

            if not (r_m == check_string_m) == celcius:
                self._units["T"] = None
                self.check_for_errors()
            self._units["RH"] = "%RH"

            if p_unit[1] in allowed_units:
                r_p = self.query(f"UNIT P {p_unit[1]}")
                check_string_p = f"P units        : {p_unit[1]}"
                if not r_p == check_string_p:
                    self.check_for_errors()
                self._units["P"] = p_unit[1]
            else:
                self.log_error(f"{p_unit[1]} is not an allowed unit {allowed_units}")

        else:  # device is of type PTB330
            self.log_error("Incorrect device class")

    @property
    def units(self):
        return self._units

    def set_format(self, format: str) -> bool:
        """Sets format of data output, e.g. 4.3 P " " 3.3 T " " 3.3 RH " " SN " " #r #n
        where x.y shows the number of digits and decimal places of the returned value;
        Here P, T, RH, and SN are placeholders for pressure, temperature, relative humidity, and serial number values;
        and " ", #r, and #n represent a string constant, carriage-return, and line feed.
        Additional allowed modifiers include ERR for error flags, U5 for unit field and (optional) length,
        TIME for time as [hh:mm:ss], and DATE for date as [yyyy-mm-dd]. For more options, refer to the manual.
        """
        self.write(f'FORM {format}')
        ok = self.read()
        if 'Output format  :' in ok:    # format is returned by some devices when set
            form = ok.strip('Output format  :').replace("\\", "#")
        elif "ok" in ok.lower():        # but if OK is returned then we need to ask for the format
            form = self.get_format()
        else:                           # this is not expected so raise an error
            self.raise_exception(ok)
            return False

        if not form.lower() == format.lower(): # the format was not set successfully
            self.check_for_errors()
            self.log_warning(f"Format of output is {form}")
            return False

        return True

    def get_format(self) -> str:
        """Return the currently active formatter string.
        The hash symbol "#" is used to set the format, but then appears as a backslash "\" on the device.
        """
        form = self.query("FORM ?").strip('Output format  :').replace("\\", "#")
        self.log_debug(f"Format of output is {form}")
        return form

    def start_run_mode(self) -> None:
        """Start continuous outputting of data (RUN mode)"""
        self.write("R")

    def stop_run_mode(self) -> None:
        """Stop continuous outputting of data (STOP mode)"""
        self.write("S")

    def get_reading_str(self) -> str:
        """Output the reading once. The returned string follows the format set by self.set_format"""
        return self.query("SEND")

    def check_for_errors(self):
        """Raise an error if present"""
        err = self.query("ERRS")  # List present transmitter errors
        # a PASS or FAIL line is returned from PTB330 modules first
        if err == "PASS":
            err = self.read()
        elif err == "FAIL":
            err = self.read()
        if err and not err == 'No errors':
            self.raise_exception(err)
